from pathlib import Path

from assets.converters.base_format.models.tokens import (
    BadgerdocToken,
    Offset,
    Page,
)
from assets.converters.pdf.pdf_converter import (  # noqa
    PlainPDFToBadgerdocTokensConverter,
)

TEST_FILES_DIR = Path(__file__).parent / "test_data"
TEST_PDF = TEST_FILES_DIR / "test.pdf"

CONVERT_RESULT_FIRST_LETTER = BadgerdocToken(
    type_="text",
    bbox=[65.8, 58.49276377952799, 71.8, 70.49276377952799],
    text="1",
    offset=Offset(begin=3, end=4),
    previous="   ",
    after=" ",
)


def test_convert() -> None:
    test_converter = PlainPDFToBadgerdocTokensConverter()
    result = test_converter.convert(TEST_PDF)
    assert isinstance(result[0], Page)
    assert result[0].objs[0] == CONVERT_RESULT_FIRST_LETTER
