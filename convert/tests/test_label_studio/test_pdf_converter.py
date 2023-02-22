from pathlib import Path
from unittest.mock import MagicMock, Mock

from pdfminer.layout import LTChar, LTTextBoxHorizontal, LTTextLineHorizontal

from src.label_studio_to_badgerdoc.badgerdoc_format.pdf_converter import (  # noqa
    PlainPDFToBadgerdocTokensConverter,
)
from src.label_studio_to_badgerdoc.models import BadgerdocToken, Offset, Page

TEST_FILES_DIR = Path(__file__).parent / "test_data"
TEST_PDF = TEST_FILES_DIR / "test.pdf"

CONVERT_RESULT_FIRST_LETTER = BadgerdocToken(
    type_="text",
    bbox=[15.0, 16.386000000000003, 21.6, 27.386000000000003],
    text="w",
    offset=Offset(begin=0, end=1),
)


class TestPlainPDFToBadgerdocTokensConverter:
    def test_get_bbox(self):
        # Set up objects
        converter = PlainPDFToBadgerdocTokensConverter()
        char_mock = Mock()
        char_mock.y1 = 16.386000000000003
        char_mock.y0 = 15.0
        converter.page_size = Mock()
        converter.page_size.height = 500

        # Call function under test
        bbox = converter.get_bbox(char_mock)

        # Verify results
        assert bbox == (
            char_mock.x0,
            500 - char_mock.y1,
            char_mock.x1,
            500 - char_mock.y0,
        )

    def test_convert_line(self):
        # Set up objects
        converter = PlainPDFToBadgerdocTokensConverter()
        converter.page_size = Mock()
        converter.page_size.height = 500
        line_mock = MagicMock()
        char_mock = MagicMock()
        char_mock.__class__ = LTChar
        char_mock.get_text.return_value = "a"
        (
            char_mock.x0,
            char_mock.x1,
            char_mock.y0,
            char_mock.y1,
        ) = CONVERT_RESULT_FIRST_LETTER.bbox

        line_mock.__iter__.return_value = [char_mock]

        # Call function under test
        tokens = converter.convert_line(line_mock)

        # Verify results
        assert tokens == [
            BadgerdocToken(
                bbox=(
                    char_mock.x0,
                    500 - char_mock.y1,
                    char_mock.x1,
                    500 - char_mock.y0,
                ),
                text="a",
                offset=Offset(begin=0, end=1),
            )
        ]

    def test_convert_page(self):
        # Set up objects
        converter = PlainPDFToBadgerdocTokensConverter()
        page_mock = MagicMock()
        page_mock.width = 200.0
        page_mock.height = 500.0
        element_mock = MagicMock()
        element_mock.__class__ = LTTextBoxHorizontal

        text_line_mock = Mock()
        text_line_mock.__class__ = LTTextLineHorizontal
        return_tokens = [CONVERT_RESULT_FIRST_LETTER]
        converter.convert_line = Mock(return_value=return_tokens)
        element_mock.__iter__.return_value = [text_line_mock]
        page_mock.__iter__.return_value = [element_mock]

        # Call function under test
        tokens = converter.convert_page(page_mock)

        # Verify results
        converter.convert_line.assert_called_once_with(text_line_mock)
        assert tokens == [CONVERT_RESULT_FIRST_LETTER]

    def test_convert(self):
        test_converter = PlainPDFToBadgerdocTokensConverter()
        result = test_converter.convert(TEST_PDF)
        assert isinstance(result, list)
        assert isinstance(result[0], Page)
        assert result[0].objs[0] == CONVERT_RESULT_FIRST_LETTER
