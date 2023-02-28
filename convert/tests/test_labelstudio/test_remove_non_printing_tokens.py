from pathlib import Path

import pytest

from src.badgerdoc_format.badgerdoc_format import BadgerdocFormat
from src.badgerdoc_format.bd_tokens_model import Page
from src.config import (
    DEFAULT_PAGE_BORDER_OFFSET,
    DEFAULT_PDF_FONT_HEIGHT,
    DEFAULT_PDF_FONT_WIDTH,
    DEFAULT_PDF_LINE_SPACING,
    DEFAULT_PDF_PAGE_WIDTH,
)
from src.plain_text_format.plain_text_converter import (
    TextToBadgerdocTokensConverter,
)


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("1 ", Page(**{
                        "size": {
                            "width": 0,
                            "height": 0
                        },
                        "page_num": 1,
                        "objs": [
                            {
                                "type": "text",
                                "bbox": [
                                    15.0,
                                    15.0,
                                    22.0,
                                    26.0
                                ],
                                "text": "1",
                                "offset": {
                                    "begin": 0,
                                    "end": 1
                                },
                                "previous": None,
                                "after": " "
                            },
                        ]
                    }
                    )),
        ("12", Page(**{
                        "size": {
                            "width": 0,
                            "height": 0
                        },
                        "page_num": 1,
                        "objs": [
                            {
                                "type": "text",
                                "bbox": [
                                    15.0,
                                    15.0,
                                    22.0,
                                    26.0
                                ],
                                "text": "1",
                                "offset": {
                                    "begin": 0,
                                    "end": 1
                                },
                                "previous": None,
                                "after": None
                            },
                            {
                                "type": "text",
                                "bbox": [
                                    22.0,
                                    15.0,
                                    29.0,
                                    26.0
                                ],
                                "text": "2",
                                "offset": {
                                    "begin": 1,
                                    "end": 2
                                },
                                "previous": None,
                                "after": None
                            },
                        ]
                    }
                    )),
        ("  1 2", Page(**{
                           "size": {
                               "width": 0,
                               "height": 0
                           },
                           "page_num": 1,
                           "objs": [
                               {
                                   "type": "text",
                                   "bbox": [
                                       29.0,
                                       15.0,
                                       36.0,
                                       26.0
                                   ],
                                   "text": "1",
                                   "offset": {
                                       "begin": 2,
                                       "end": 3
                                   },
                                   "previous": "  ",
                                   "after": " "
                               },
                               {
                                   "type": "text",
                                   "bbox": [
                                       43.0,
                                       15.0,
                                       50.0,
                                       26.0
                                   ],
                                   "text": "2",
                                   "offset": {
                                       "begin": 4,
                                       "end": 5
                                   }
                               },
                           ]
                       }
                       )
         ),
        (" \n1 2", Page(**{
                           "size": {
                               "width": 0,
                               "height": 0
                           },
                           "page_num": 1,
                           "objs": [
                               {
                                   "type": "text",
                                   "bbox": [
                                       15.0,
                                       48.0,
                                       22.0,
                                       59.0
                                   ],
                                   "text": "1",
                                   "offset": {
                                       "begin": 2,
                                       "end": 3
                                   },
                                   "previous": " \n",
                                   "after": " "
                               },
                               {
                                   "type": "text",
                                   "bbox": [
                                       29.0,
                                       48.0,
                                       36.0,
                                       59.0
                                   ],
                                   "text": "2",
                                   "offset": {
                                       "begin": 4,
                                       "end": 5
                                   }
                               },
                           ]
                       }
                       )
         ),
        ("1", Page(**{
                           "size": {
                               "width": 0,
                               "height": 0
                           },
                           "page_num": 1,
                           "objs": [
                               {
                                   "type": "text",
                                   "bbox": [
                                       15.0,
                                       15.0,
                                       22.0,
                                       26.0
                                   ],
                                   "text": "1",
                                   "offset": {
                                       "begin": 0,
                                       "end": 1
                                   },
                                   "previous": None,
                                   "after": None
                               },
                           ]
                       }
                       )
         ),
        # ("", Page(**{
        #                    "size": {
        #                        "width": 0,
        #                        "height": 0
        #                    },
        #                    "page_num": 1,
        #                    "objs": [
        #                    ]
        #                }
        #                )
        #  ),
    ]
)
def test_plain_text_converter(test_input: str, expected: Page, tmp_path):
    converter = TextToBadgerdocTokensConverter(
        page_width=DEFAULT_PDF_PAGE_WIDTH,
        page_border_offset=DEFAULT_PAGE_BORDER_OFFSET,
        font_height=DEFAULT_PDF_FONT_HEIGHT,
        font_width=DEFAULT_PDF_FONT_WIDTH,
        line_spacing=DEFAULT_PDF_LINE_SPACING,
    )
    tokens = converter.convert(test_input)

    bd_format = BadgerdocFormat()
    bd_format.tokens_page = tokens
    bd_format.export_pdf(tmp_path / "tmp.pdf")
    bd_format.remove_non_printing_tokens()

    assert len(bd_format.tokens_page.objs) == len(expected.objs)
    for test_obj, expected_obj in zip(expected.objs, bd_format.tokens_page.objs):
        assert test_obj == expected_obj
