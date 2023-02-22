from pathlib import Path

from src.badgerdoc_format.bd_tokens_model import BadgerdocToken, Offset, Page
from src.pdf_format.pdf_converter import (  # noqa
    PlainPDFToBadgerdocTokensConverter,
)

TEST_FILES_DIR = Path(__file__).parent / "test_data"
TEST_PDF = TEST_FILES_DIR / "test.pdf"

CONVERT_RESULT_FIRST_LETTER = BadgerdocToken(
    type_="text",
    bbox=[15.0, 16.386000000000003, 21.6, 27.386000000000003],
    text="w",
    offset=Offset(begin=0, end=1),
)


def test_convert():
    test_converter = PlainPDFToBadgerdocTokensConverter()
    result = test_converter.convert(TEST_PDF)
    assert isinstance(result[0], Page)
    assert result[0].objs[0] == CONVERT_RESULT_FIRST_LETTER
