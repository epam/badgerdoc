from pathlib import Path

from convert.converters.base_format.models.tokens import Page
from convert.converters.pdf.pdf_converter import (
    PlainPDFToBadgerdocTokensConverter,
    PlainPDFToBadgerdocTokensConverterPytz,
)

TEST_FILES_DIR = Path(__file__).parent / "data"
TEST_PDF = TEST_FILES_DIR / "12.pdf"

etalon = Page.parse_file(TEST_FILES_DIR / "badgerdoc/1.json")
etalon_pytz = Page.parse_file(TEST_FILES_DIR / "badgerdoc/2.json")


def test_convert() -> None:
    test_converter = PlainPDFToBadgerdocTokensConverter()
    result = test_converter.convert(TEST_PDF)
    assert isinstance(result[0], Page)
    assert result[0] == etalon


def test_convert_pytz() -> None:
    test_converter = PlainPDFToBadgerdocTokensConverterPytz()
    result = test_converter.convert(TEST_PDF)
    assert isinstance(result[0], Page)
    assert result[0] == etalon_pytz
