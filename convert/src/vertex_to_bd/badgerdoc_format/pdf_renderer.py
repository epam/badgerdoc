from enum import Enum
from pathlib import Path
from typing import List

import fitz

from ..models import BadgerdocToken


class Fonts(Enum):
    COURIER = "cour"


class PDFRenderer:
    def __init__(
        self,
        page_border_offset: int = 15,
        font_name: str = Fonts.COURIER.value,
        font_size: int = 11,
    ):
        self.page_border_offset = page_border_offset
        self.font_name = font_name
        self.font_size = font_size

    def render_tokens(
        self, tokens: List[BadgerdocToken], save_path: Path
    ) -> None:
        doc = fitz.open()
        width = (
            max((token.bbox[2] for token in tokens)) + self.page_border_offset
        )
        height = (
            max((token.bbox[3] for token in tokens)) + self.page_border_offset
        )
        page = doc.new_page(height=height, width=width)
        for token in tokens:
            self._draw_token(token, page)
        doc.save(save_path)

    def _draw_token(self, token: BadgerdocToken, page: fitz.Page) -> None:
        rect = fitz.Rect(token.bbox)
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(width=0.3, color=(0.8, 0.8, 1))
        shape.insert_textbox(
            rect, token.text, fontname=self.font_name, fontsize=self.font_size
        )
        shape.commit()
