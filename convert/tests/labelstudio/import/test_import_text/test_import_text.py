import json
from pathlib import Path

from convert.config import (
    DEFAULT_PAGE_BORDER_OFFSET,
    DEFAULT_PDF_FONT_HEIGHT,
    DEFAULT_PDF_FONT_WIDTH,
    DEFAULT_PDF_LINE_SPACING,
    DEFAULT_PDF_PAGE_WIDTH,
)
from convert.converters.text.text_to_tokens_converter import (
    TextToBadgerdocTokensConverter,
)

from convert.converters.labelstudio.labelstudio_to_badgerdoc_converter import ConverterToBadgerdoc
from convert.converters.base_format.badgerdoc import Badgerdoc

TEST_FILES_DIR = Path(__file__).parent / "data_text"

INPUT_LABELSTUDIO_FILE = TEST_FILES_DIR / "input_text_field.json"
BADGERDOC_TOKENS_FILE = TEST_FILES_DIR / "badgerdoc_tokens.json"


def test_plain_text_converter() -> None:
    labelstudio_data = json.loads(INPUT_LABELSTUDIO_FILE.read_text())
    converter = TextToBadgerdocTokensConverter(
        page_width=DEFAULT_PDF_PAGE_WIDTH,
        page_border_offset=DEFAULT_PAGE_BORDER_OFFSET,
        font_height=DEFAULT_PDF_FONT_HEIGHT,
        font_width=DEFAULT_PDF_FONT_WIDTH,
        line_spacing=DEFAULT_PDF_LINE_SPACING,
    )
    tokens = converter.convert(labelstudio_data["text"])
    expected_bd_tokens = json.loads(Path(BADGERDOC_TOKENS_FILE).read_text())

    badgerdoc_format = Badgerdoc()
    badgerdoc_format.tokens_page = tokens
    badgerdoc_format.remove_non_printing_tokens()
    assert tokens.dict(by_alias=True, exclude_none=True) == expected_bd_tokens
