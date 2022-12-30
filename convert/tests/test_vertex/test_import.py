import json
from pathlib import Path
from tempfile import TemporaryDirectory

from src.vertex_to_bd.models import BadgerdocToken, LabelStudioModel
from src.vertex_to_bd.badgerdoc_format.pdf_renderer import PDFRenderer
from src.vertex_to_bd.badgerdoc_format.badgerdoc_format import BadgerdocFormat
from src.vertex_to_bd.badgerdoc_format.plain_text_converter import (
    PlainTextToBadgerdocTokenConverter,
)

# TODO: it's not real tests

TEST_FILES_DIR = Path(__file__).parent / "test_data"

INPUT_VERTEX_FILE = TEST_FILES_DIR / "input_text_field.json"
INPUT_LABELSTUDIO_FILE = TEST_FILES_DIR / "label_studio_format.json"
BADGERDOC_TOKENS_FILE = TEST_FILES_DIR / "badgerdoc_tokens.json"
BADGERDOC_ANNOTATIONS_FILE = TEST_FILES_DIR / "badgerdoc_annotation.json"
TEST_PDF = TEST_FILES_DIR / "test.pdf"


def test_plain_text_converter():
    vertex_data = json.loads(INPUT_VERTEX_FILE.read_text())
    converter = PlainTextToBadgerdocTokenConverter(
        page_width=595,
        page_border_offset=15,
        font_height=11,
        font_width=7,
        line_spacing=2,
    )
    tokens = converter.convert(vertex_data["text"])
    expected_bd_tokens = json.loads(Path(BADGERDOC_TOKENS_FILE).read_text())
    assert tokens.dict(by_alias=True) == expected_bd_tokens


def test_render_pdf():
    tokens = json.loads(Path(BADGERDOC_TOKENS_FILE).read_text())["objs"]
    bd_tokens = [BadgerdocToken(**token) for token in tokens]
    with TemporaryDirectory() as dir_name:
        pdf_file_path = Path(dir_name) / "generated.pdf"
        PDFRenderer(15).render_tokens(bd_tokens, pdf_file_path)
        assert (
            TEST_PDF.read_bytes()[:1500] == pdf_file_path.read_bytes()[:1500]
        )


def test_annotation_converter():
    badgerdoc_format = BadgerdocFormat(
        page_width=595,
        page_border_offset=15,
        font_height=11,
        font_width=7,
        line_spacing=2,
    )
    badgerdoc_format.convert_from_labelstudio(LabelStudioModel.parse_file(INPUT_LABELSTUDIO_FILE))
    badgerdoc_format.export_tokens(Path("tokens_test.json"))
    badgerdoc_format.export_pdf(Path("pdf_test.pdf"))
