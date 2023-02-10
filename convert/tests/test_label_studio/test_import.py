import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.config import (
    DEFAULT_PAGE_BORDER_OFFSET,
    DEFAULT_PDF_FONT_HEIGHT,
    DEFAULT_PDF_FONT_WIDTH,
    DEFAULT_PDF_LINE_SPACING,
    DEFAULT_PDF_PAGE_WIDTH,
)
from src.label_studio_to_badgerdoc.badgerdoc_format.badgerdoc_format import (
    BadgerdocFormat,
)
from src.label_studio_to_badgerdoc.badgerdoc_format.plain_text_converter import (
    TextToBadgerdocTokensConverter,
)
from src.label_studio_to_badgerdoc.models.label_studio_models import (
    LabelStudioModel,
)

TEST_FILES_DIR = Path(__file__).parent / "test_data"

INPUT_LABEL_STUDIO_FILE = TEST_FILES_DIR / "input_text_field.json"
INPUT_LABELSTUDIO_FILE = TEST_FILES_DIR / "label_studio_format.json"
BADGERDOC_TOKENS_FILE = TEST_FILES_DIR / "badgerdoc_tokens.json"
TEST_PDF = TEST_FILES_DIR / "test.pdf"


def test_plain_text_converter():
    label_studio_data = json.loads(INPUT_LABEL_STUDIO_FILE.read_text())
    converter = TextToBadgerdocTokensConverter(
        page_width=DEFAULT_PDF_PAGE_WIDTH,
        page_border_offset=DEFAULT_PAGE_BORDER_OFFSET,
        font_height=DEFAULT_PDF_FONT_HEIGHT,
        font_width=DEFAULT_PDF_FONT_WIDTH,
        line_spacing=DEFAULT_PDF_LINE_SPACING,
    )
    tokens = converter.convert(label_studio_data["text"])
    expected_bd_tokens = json.loads(Path(BADGERDOC_TOKENS_FILE).read_text())
    assert tokens.dict(by_alias=True) == expected_bd_tokens


# def test_render_pdf():
#     # TODO write proper comparator
#     tokens = json.loads(Path(BADGERDOC_TOKENS_FILE).read_text())["objs"]
#     bd_tokens = [BadgerdocToken(**token) for token in tokens]
#     with TemporaryDirectory() as dir_name:
#         pdf_file_path = Path(dir_name) / "generated.pdf"
#         PDFRenderer(15).render_tokens(bd_tokens, pdf_file_path)
#         assert (
#             TEST_PDF.read_bytes()[:1500] == pdf_file_path.read_bytes()[:1500]
#         )


def test_annotation_converter():
    badgerdoc_format = BadgerdocFormat(
        page_width=595,
        page_border_offset=15,
        font_height=11,
        font_width=7,
        line_spacing=2,
    )

    badgerdoc_format.convert_from_labelstudio(
        LabelStudioModel.parse_file(INPUT_LABELSTUDIO_FILE)
    )
    with TemporaryDirectory() as dir_name:
        tokens_test_path = Path(dir_name) / "tokens_test.json"
        annotations_test_path = Path(dir_name) / "annotations_test.json"
        badgerdoc_format.export_tokens(tokens_test_path)
        badgerdoc_format.export_annotations(annotations_test_path)
        tokens_test = json.loads(tokens_test_path.read_text())
        annotations_test = json.loads(annotations_test_path.read_text())

        tokens_etalon_path = (
            TEST_FILES_DIR / "badgerdoc_etalon" / "tokens_test.json"
        )
        annotations_etalon_path = (
            TEST_FILES_DIR / "badgerdoc_etalon" / "annotations_test.json"
        )
        tokens_etalon = json.loads(tokens_etalon_path.read_text())
        annotations_etalon = json.loads(annotations_etalon_path.read_text())
        assert tokens_test == tokens_etalon
        assert annotations_test == annotations_etalon


def test_import_document_links():
    badgerdoc_format = BadgerdocFormat(
        page_width=595,
        page_border_offset=15,
        font_height=11,
        font_width=7,
        line_spacing=2,
    )

    badgerdoc_format.convert_from_labelstudio(
        LabelStudioModel.parse_file(INPUT_LABELSTUDIO_FILE)
    )
    with TemporaryDirectory() as dir_name:
        tokens_test_path = Path(dir_name) / "tokens_test.json"
        annotations_test_path = Path(dir_name) / "annotations_test.json"
        badgerdoc_format.export_tokens(tokens_test_path)
        badgerdoc_format.export_annotations(annotations_test_path)
        tokens_test = json.loads(tokens_test_path.read_text())
        annotations_test = json.loads(annotations_test_path.read_text())

        tokens_etalon_path = (
            TEST_FILES_DIR / "badgerdoc_etalon" / "tokens_test.json"
        )
        annotations_etalon_path = (
            TEST_FILES_DIR / "badgerdoc_etalon" / "annotations_test.json"
        )
        tokens_etalon = json.loads(tokens_etalon_path.read_text())
        annotations_etalon = json.loads(annotations_etalon_path.read_text())
        assert tokens_test == tokens_etalon
        assert annotations_test == annotations_etalon
