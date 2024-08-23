from enum import Enum
from pathlib import Path
from typing import List

import fitz
from fitz import Page

from .models.tokens import BadgerdocToken

DEFAULT_PAGE_BORDER_OFFSET = 15
DEFAULT_PDF_FONT_HEIGHT = 11


class Fonts(Enum):
    COURIER = "cour"
    FIMO = "fimo"


class PDFRenderer:
    def __init__(
        self,
        page_border_offset: int = DEFAULT_PAGE_BORDER_OFFSET,
        font_name: str = Fonts.FIMO.value,
        font_size: int = DEFAULT_PDF_FONT_HEIGHT,
    ):
        self.page_border_offset = page_border_offset
        self.font_name = font_name
        self.font_size = font_size

    def render_tokens(
        self, tokens: List[BadgerdocToken], save_path: Path
    ) -> None:
        with fitz.open() as doc:
            width = (
                max(token.bbox[2] for token in tokens)
                + self.page_border_offset
            )
            height = (
                max(token.bbox[3] for token in tokens)
                + self.page_border_offset
            )

            page = doc.new_page(height=height, width=width)
            for token in tokens:
                self._draw_token(token, self.font_name, page)
            doc.save(save_path)

    def _draw_token(
        self, token: BadgerdocToken, font_name: str, page: Page
    ) -> None:
        rect = fitz.Rect(token.bbox)
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.insert_textbox(
            rect, token.text, fontname=font_name, fontsize=self.font_size
        )
        shape.commit()
