from typing import List

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextBoxHorizontal, LTTextLineHorizontal

from src.label_studio_to_badgerdoc.models import (
    BadgerdocToken,
    Offset,
    Page,
    PageSize,
)
from src.label_studio_to_badgerdoc.models.bd_tokens_model import Pages


class PlainPDFToBadgerdocTokensConverter:
    def __init__(self):
        self.offset = 0

    @staticmethod
    def line_tokens_amount(line) -> int:
        token_size = line.font_width
        return (line.page_width - line.page_border_offset * 2) // token_size

    def convert_line(self, line: LTTextLineHorizontal) -> List[BadgerdocToken]:
        tokens = []
        for i, char in enumerate(line):
            if isinstance(char, LTChar):
                tokens.append(
                    BadgerdocToken(
                        bbox=char.bbox,
                        text=char.get_text(),
                        offset=Offset(begin=self.offset, end=self.offset + 1),
                    )
                )
                self.offset += 1
        return tokens

    def convert(self, plain_pfd) -> Pages:
        pages = []
        with open(plain_pfd, mode="rb") as pdf_obj:
            for page in extract_pages(pdf_obj):
                tokens = []
                for element in page:
                    if isinstance(element, LTTextBoxHorizontal):
                        for line in element:
                            if isinstance(line, LTTextLineHorizontal):
                                tokens.extend(self.convert_line(line))
                page_size = PageSize(width=page.width, height=page.width)
                pages.append(
                    Page(page_num=page.pageid, size=page_size, objs=tokens)
                )
        return Pages(pages=pages)
