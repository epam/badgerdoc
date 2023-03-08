from typing import List

from assets.converters.base_format.models.tokens import (
    BadgerdocToken,
    Offset,
    Page,
    PageSize,
)
from assets.converters.utils import filter_printing_tokens
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextBoxHorizontal, LTTextLineHorizontal


class PlainPDFToBadgerdocTokensConverter:
    def __init__(self):
        self.offset = 0
        self.page_size = None

    def get_bbox(self, char: LTChar) -> tuple:
        return (
            char.x0,
            self.page_size.height - char.y1,
            char.x1,
            self.page_size.height - char.y0,
        )

    def convert_line(self, line: LTTextLineHorizontal) -> List[BadgerdocToken]:
        tokens = []
        for char in line:
            if not isinstance(char, LTChar):
                continue
            tokens.append(
                BadgerdocToken(
                    bbox=self.get_bbox(char),
                    text=char.get_text(),
                    offset=Offset(begin=self.offset, end=self.offset + 1),
                )
            )
            self.offset += 1
        return tokens

    def convert_page(self, page: Page) -> List[BadgerdocToken]:
        tokens = []
        self.page_size = PageSize(width=page.width, height=page.height)
        for element in page:
            if not isinstance(element, LTTextBoxHorizontal):
                continue
            for line in element:
                if not isinstance(line, LTTextLineHorizontal):
                    continue
                tokens.extend(self.convert_line(line))
        return filter_printing_tokens(tokens)

    def convert(self, plain_pfd) -> List[Page]:
        with open(plain_pfd, mode="rb") as pdf_obj:
            return [
                Page(
                    page_num=i,
                    objs=self.convert_page(page),
                    size=self.page_size,
                )
                for i, page in enumerate(extract_pages(pdf_obj), start=1)
            ]
