from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from PIL import Image

from badgerdoc import chunk_xpath
from badgerdoc.models import document
from badgerdoc.tests.settings import mock_db_and_file_storage

HOCR_CONTENT = (
    "<html><body>"
    "<div class='ocr_page' id='page_1'>"
    "<div class='ocr_carea' id='block_1_1' title='bbox 142 107 543 197'>"
    "<p class='ocr_par'>Sample text</p></div>"
    "<div class='ocr_carea' id='block_1_2' title='bbox 10 20 30 40; ppageno 1'>"
    "<p class='ocr_par'>Other text</p></div>"
    "</div></body></html>"
)


class ExtractBboxFromHocrTestCase(TestCase):
    def test_extracts_bbox(self):
        result = chunk_xpath.extract_bbox_from_hocr(
            HOCR_CONTENT, "//div[@id='block_1_1']"
        )
        self.assertEqual(result, (142, 107, 543, 197))

    def test_extracts_bbox_with_mixed_title(self):
        result = chunk_xpath.extract_bbox_from_hocr(
            HOCR_CONTENT, "//div[@id='block_1_2']"
        )
        self.assertEqual(result, (10, 20, 30, 40))

    def test_raises_on_empty_content(self):
        with self.assertRaises(ValueError):
            chunk_xpath.extract_bbox_from_hocr("", "//div[@id='block_1_1']")

    def test_raises_when_xpath_no_match(self):
        with self.assertRaises(ValueError):
            chunk_xpath.extract_bbox_from_hocr(
                HOCR_CONTENT, "//div[@id='nonexistent']"
            )

    def test_raises_when_element_has_no_title(self):
        content = "<html><body><div id='notitle'>text</div></body></html>"
        with self.assertRaises(ValueError):
            chunk_xpath.extract_bbox_from_hocr(content, "//div[@id='notitle']")

    def test_raises_when_title_has_no_bbox(self):
        content = "<html><body><div id='x' title='ppageno 1'>text</div></body></html>"
        with self.assertRaises(ValueError):
            chunk_xpath.extract_bbox_from_hocr(content, "//div[@id='x']")

    def test_raises_when_xpath_matches_text_node(self):
        with self.assertRaises(ValueError):
            chunk_xpath.extract_bbox_from_hocr(
                HOCR_CONTENT, "//div[@id='block_1_1']/p/text()"
            )


def _make_png_bytes(width=100, height=100, color=(255, 0, 0)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class CropImageTestCase(TestCase):
    def test_returns_png_bytes(self):
        png_bytes = _make_png_bytes()
        result = chunk_xpath.crop_image(png_bytes, 0, 0, 50, 50)
        self.assertTrue(result.startswith(b"\x89PNG"))

    def test_crops_to_correct_dimensions(self):
        png_bytes = _make_png_bytes(100, 100)
        result = chunk_xpath.crop_image(png_bytes, 10, 20, 50, 60)
        img = Image.open(BytesIO(result))
        self.assertEqual(img.size, (40, 40))


class ScaleHocrToPixelsTestCase(TestCase):
    def test_scales_full_range_to_full_image(self):
        result = chunk_xpath._scale_hocr_to_pixels(
            (0, 0, 1000, 1000), 800, 600
        )
        self.assertEqual(result, (0, 0, 800, 600))

    def test_scales_half_range(self):
        result = chunk_xpath._scale_hocr_to_pixels((0, 0, 500, 500), 800, 600)
        self.assertEqual(result, (0, 0, 400, 300))

    def test_scales_arbitrary_coords(self):
        result = chunk_xpath._scale_hocr_to_pixels(
            (100, 200, 600, 800), 1000, 2000
        )
        self.assertEqual(result, (100, 400, 600, 1600))

    def test_rounds_fractional_pixels(self):
        result = chunk_xpath._scale_hocr_to_pixels((1, 1, 999, 999), 100, 100)
        self.assertEqual(
            result,
            (
                round(1 * 100 / 1000),
                round(1 * 100 / 1000),
                round(999 * 100 / 1000),
                round(999 * 100 / 1000),
            ),
        )


@mock_db_and_file_storage
class FindExistingChunkTestCase(TestCase):
    def setUp(self):
        self.trigger_workflow_patch = patch(
            "badgerdoc.signals.trigger_automatic.workflow.trigger"
        )
        self.mock_trigger_workflow = self.trigger_workflow_patch.start()
        patch(
            "badgerdoc.signals.workflow.get_supported_workflows",
            return_value=[],
        ).start()

        self.owner = User.objects.create_user(
            username="owner", email="owner@test.com", password="testpass123"
        )
        self.parent = document.Document.objects.create(
            uploaded_by=self.owner,
            name="parent_doc",
            extension="png",
        )
        self.chunk = document.Document.objects.create(
            uploaded_by=self.owner,
            name="parent_doc_chunk_p1_10_20_30_40",
            extension="png",
            parent_document=self.parent,
            tags=["chunk"],
            metadata={"page": 1, "position_in_parent": "10 20 30 40"},
        )

    def tearDown(self):
        self.trigger_workflow_patch.stop()

    def test_returns_existing_chunk(self):
        result = chunk_xpath.find_existing_chunk(
            self.parent.id, 1, "10 20 30 40"
        )
        self.assertEqual(result, self.chunk)

    def test_returns_none_when_not_found(self):
        result = chunk_xpath.find_existing_chunk(
            self.parent.id, 1, "99 99 99 99"
        )
        self.assertIsNone(result)

    def test_returns_none_for_wrong_document_id(self):
        result = chunk_xpath.find_existing_chunk(
            self.parent.id + 9999, 1, "10 20 30 40"
        )
        self.assertIsNone(result)

    def test_returns_none_for_wrong_page(self):
        result = chunk_xpath.find_existing_chunk(
            self.parent.id, 2, "10 20 30 40"
        )
        self.assertIsNone(result)


@mock_db_and_file_storage
class CreateChunkDocumentTestCase(TestCase):
    def setUp(self):
        self.trigger_workflow_patch = patch(
            "badgerdoc.signals.trigger_automatic.workflow.trigger"
        )
        self.mock_trigger_workflow = self.trigger_workflow_patch.start()
        patch(
            "badgerdoc.signals.workflow.get_supported_workflows",
            return_value=[],
        ).start()

        self.owner = User.objects.create_user(
            username="owner", email="owner@test.com", password="testpass123"
        )
        self.parent_doc = document.Document.objects.create(
            uploaded_by=self.owner,
            name="test_doc",
            extension="png",
        )

    def tearDown(self):
        self.trigger_workflow_patch.stop()

    def _minimal_png_bytes(self) -> bytes:
        img = Image.new("RGB", (1, 1), color=(0, 0, 0))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_creates_document_with_chunk_tag(self):
        png_bytes = self._minimal_png_bytes()
        result = chunk_xpath.create_chunk_document(
            self.parent_doc, self.owner, 1, 5, 10, 50, 60, png_bytes
        )
        self.assertEqual(result.tags, ["chunk"])

    def test_creates_document_with_coordinates_in_metadata(self):
        png_bytes = self._minimal_png_bytes()
        result = chunk_xpath.create_chunk_document(
            self.parent_doc, self.owner, 1, 5, 10, 50, 60, png_bytes
        )
        self.assertEqual(
            result.metadata, {"page": 1, "position_in_parent": "5 10 50 60"}
        )

    def test_creates_document_linked_to_parent(self):
        png_bytes = self._minimal_png_bytes()
        result = chunk_xpath.create_chunk_document(
            self.parent_doc, self.owner, 1, 5, 10, 50, 60, png_bytes
        )
        self.assertEqual(result.parent_document, self.parent_doc)

    def test_creates_document_with_correct_name(self):
        png_bytes = self._minimal_png_bytes()
        result = chunk_xpath.create_chunk_document(
            self.parent_doc, self.owner, 1, 5, 10, 50, 60, png_bytes
        )
        self.assertEqual(result.name, "test_doc_chunk_p1_5_10_50_60")

    def test_creates_document_with_png_extension(self):
        png_bytes = self._minimal_png_bytes()
        result = chunk_xpath.create_chunk_document(
            self.parent_doc, self.owner, 1, 5, 10, 50, 60, png_bytes
        )
        self.assertEqual(result.extension, "png")


@mock_db_and_file_storage
class CropRenditionTestCase(TestCase):
    def setUp(self):
        self.trigger_workflow_patch = patch(
            "badgerdoc.signals.trigger_automatic.workflow.trigger"
        )
        self.mock_trigger_workflow = self.trigger_workflow_patch.start()
        patch(
            "badgerdoc.signals.workflow.get_supported_workflows",
            return_value=[],
        ).start()

        self.owner = User.objects.create_user(
            username="owner", email="owner@test.com", password="testpass123"
        )

    def tearDown(self):
        self.trigger_workflow_patch.stop()

    def _make_rendition(self, metadata: dict) -> document.Document:
        png_bytes = _make_png_bytes(width=200, height=100)
        rendition = document.Document.objects.create(
            uploaded_by=self.owner,
            name="rendition",
            extension="png",
            tags=["rendition"],
            metadata=metadata,
        )
        rendition.file.save("rendition.png", BytesIO(png_bytes), save=True)
        return rendition

    def test_happy_path_returns_png_and_crops_correctly(self):
        rendition = self._make_rendition(
            {"page": 1, "size": {"width": 200, "height": 100}}
        )
        result = chunk_xpath.crop_rendition(rendition, 0, 0, 500, 500)
        img = Image.open(BytesIO(result))
        self.assertEqual(img.size, (100, 50))

    def test_raises_when_metadata_is_none(self):
        rendition = self._make_rendition({})
        with self.assertRaises(chunk_xpath.RenditionMissingSizeError):
            chunk_xpath.crop_rendition(rendition, 0, 0, 500, 500)

    def test_raises_when_size_key_missing(self):
        rendition = self._make_rendition({"page": 1})
        with self.assertRaises(chunk_xpath.RenditionMissingSizeError):
            chunk_xpath.crop_rendition(rendition, 0, 0, 500, 500)

    def test_raises_when_size_missing_width(self):
        rendition = self._make_rendition({"page": 1, "size": {"height": 100}})
        with self.assertRaises(chunk_xpath.RenditionMissingSizeError):
            chunk_xpath.crop_rendition(rendition, 0, 0, 500, 500)

    def test_raises_when_size_missing_height(self):
        rendition = self._make_rendition({"page": 1, "size": {"width": 200}})
        with self.assertRaises(chunk_xpath.RenditionMissingSizeError):
            chunk_xpath.crop_rendition(rendition, 0, 0, 500, 500)
