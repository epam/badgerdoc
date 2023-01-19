import json
import pprint
from pathlib import Path

from src.config import (
    DEFAULT_PAGE_BORDER_OFFSET,
    DEFAULT_PDF_FONT_HEIGHT,
    DEFAULT_PDF_FONT_WIDTH,
    DEFAULT_PDF_LINE_SPACING,
    DEFAULT_PDF_PAGE_WIDTH,
)
from src.label_studio_to_badegerdoc.badgerdoc_format.badgerdoc_format import BadgerdocFormat
from src.label_studio_to_badegerdoc.badgerdoc_format.plain_text_converter import (
    TextToBadgerdocTokensConverter,
)
from src.label_studio_to_badegerdoc.models.label_studio_models import LabelStudioModel

TEST_FILES_DIR = Path(__file__).parent / "test_data"

INPUT_VERTEX_FILE = TEST_FILES_DIR / "input_text_field.json"
INPUT_LABELSTUDIO_FILE = TEST_FILES_DIR / "label_studio_format.json"
BADGERDOC_TOKENS_FILE = TEST_FILES_DIR / "badgerdoc_tokens.json"
BADGERDOC_ANNOTATIONS_FILE = TEST_FILES_DIR / "badgerdoc_annotation.json"
TEST_PDF = TEST_FILES_DIR / "test.pdf"


def test_plain_text_converter():
    label_studio_data = json.loads(INPUT_VERTEX_FILE.read_text())
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
    badgerdoc_format.export_tokens(Path("tokens_test.json"))
    badgerdoc_format.export_annotations(Path("annotations_test.json"))
    badgerdoc_format.export_pdf(Path("pdf_test.pdf"))

    pprint.pprint(json.loads(Path("annotations_test.json").read_text()))
