from pathlib import Path
from typing import List, Optional

from pdfminer.high_level import extract_pages
from pdfminer.layout import (
    LTAnno,
    LTChar,
    LTPage,
    LTTextBoxHorizontal,
    LTTextLineHorizontal,
)

from assets.utils.convert.badgerdoc import filter_printing_tokens

from .models.tokens import BadgerdocToken, Bbox, Offset, Page, PageSize


class PlainPDFToBadgerdocTokensConverter:
    def __init__(self) -> None:
        self.offset = 0
        self.page_size: Optional[PageSize] = None

    def convert(self, plain_pdf: Path) -> List[Page]:
        pages = []
        with open(plain_pdf, mode="rb") as pdf_obj:
            for i, page in enumerate(extract_pages(pdf_obj), start=1):
                page_objs = self._convert_page(page)
                if not self.page_size:
                    continue
                pages.append(
                    Page(
                        page_num=i,
                        objs=page_objs,
                        size=self.page_size,
                    )
                )
            return pages

    def _convert_page(self, page: LTPage) -> List[BadgerdocToken]:
        tokens = []
        self.page_size = PageSize(width=page.width, height=page.height)
        for element in page:
            if not isinstance(element, LTTextBoxHorizontal):
                continue
            for line in element:
                if not isinstance(line, LTTextLineHorizontal):
                    continue
                tokens.extend(self._convert_line(line))
        return filter_printing_tokens(tokens)

    def _convert_line(
        self, line: LTTextLineHorizontal
    ) -> List[BadgerdocToken]:
        tokens: List[BadgerdocToken] = []
        for char in line:
            char_with_bbox = isinstance(char, LTChar)
            char_without_bbox = isinstance(char, LTAnno)
            if char_with_bbox:
                bbox = self._get_char_bbox(char)
            elif char_without_bbox:
                bbox = self._form_virtrual_symbol_bbox(tokens, line)
            else:
                continue
            tokens.append(
                BadgerdocToken(
                    bbox=bbox,
                    text=char.get_text(),
                    offset=Offset(begin=self.offset, end=self.offset + 1),
                )
            )
            self.offset += 1
        return tokens

    def _get_char_bbox(self, char: LTChar) -> Bbox:
        if not self.page_size:
            raise AttributeError("Page size isn't initialized")
        x0, y0, x1, y1 = map(float, (char.x0, char.y0, char.x1, char.y1))
        return x0, self.page_size.height - y1, x1, self.page_size.height - y0

    def _form_virtrual_symbol_bbox(
        self,
        line_tokens: List[BadgerdocToken],
        line: LTTextLineHorizontal,
    ) -> Bbox:
        if line_tokens:
            return self._create_neighbor_bbox(line_tokens[-1].bbox)
        return self._get_char_bbox(line.bbox)

    def _create_neighbor_bbox(self, current_bbox: Bbox) -> Bbox:
        (
            x0,
            y0,
            x1,
            y1,
        ) = current_bbox
        new_x0, new_y0 = x1, y0
        new_x1, new_y1 = (x1 - x0) + x1, y1
        return new_x0, new_y0, new_x1, new_y1
