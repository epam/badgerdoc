from pathlib import Path
from typing import List, Optional, Tuple

from pdfminer.high_level import extract_pages
from pdfminer.layout import (
    LTChar,
    LTPage,
    LTTextBoxHorizontal,
    LTTextLineHorizontal,
)

from convert.converters.base_format.models.tokens import (
    BadgerdocToken,
    Offset,
    Page,
    PageSize,
)
from convert.converters.utils import filter_printing_tokens


class PlainPDFToBadgerdocTokensConverter:
    def __init__(self) -> None:
        self.offset = 0
        self.page_size: Optional[PageSize] = None

    def get_bbox(self, char: LTChar) -> Tuple[float, float, float, float]:
        if not self.page_size:
            raise AttributeError("Page size isn't initialized")
        return (
            float(char.x0),
            float(self.page_size.height - char.y1),
            float(char.x1),
            float(self.page_size.height - char.y0),
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

    def convert_page(self, page: LTPage) -> List[BadgerdocToken]:
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

    def convert(self, plain_pdf: Path) -> List[Page]:
        with open(plain_pdf, mode="rb") as pdf_obj:
            pages = []
            for i, page in enumerate(extract_pages(pdf_obj), start=1):
                objs = self.convert_page(page)
                if not self.page_size:
                    continue
                pages.append(
                    Page(
                        page_num=i,
                        objs=objs,
                        size=self.page_size,
                    )
                )
            return pages
