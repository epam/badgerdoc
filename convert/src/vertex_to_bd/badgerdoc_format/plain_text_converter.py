from typing import List

from ...config import (
    DEFAULT_PAGE_BORDER_OFFSET,
    DEFAULT_PDF_FONT_HEIGHT,
    DEFAULT_PDF_FONT_WIDTH,
    DEFAULT_PDF_LINE_SPACING,
    DEFAULT_PDF_PAGE_WIDTH,
)
from ..models import BadgerdocToken, Offset, Page, PageSize


def generate_chunks(text: str, size: int = 70) -> List[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


class TextToBadgerdocTokensConverter:
    # TODO: calculate font width by font_height
    def __init__(
        self,
        page_width: int = DEFAULT_PDF_PAGE_WIDTH,
        font_height: int = DEFAULT_PDF_FONT_HEIGHT,
        font_width: int = DEFAULT_PDF_FONT_WIDTH,
        line_spacing: int = DEFAULT_PDF_LINE_SPACING,
        page_border_offset: int = DEFAULT_PAGE_BORDER_OFFSET,
    ) -> None:

        self.page_width = page_width
        self.page_border_offset = page_border_offset
        self.font_height = font_height
        self.font_width = font_width
        self.line_spacing = line_spacing

    def convert(self, text: str) -> Page:
        paragraphs = self._get_paragraphs(text)

        tokens = []
        line_offset = 0
        y = self.page_border_offset
        for paragraph in paragraphs:
            lines = generate_chunks(paragraph, self.line_tokens_amount)
            for line in lines:
                self.convert_line(line, tokens, y, line_offset=line_offset)
                y += self.font_height * self.line_spacing
                line_offset += len(line)
            y += self.font_height

        page_size = self.calculate_page_size(tokens, self.page_border_offset)
        return Page(page_num=1, size=page_size, objs=tokens)

    def _get_paragraphs(self, text: str) -> List[str]:
        paragraphs = [paragraph + "\n" for paragraph in text.split("\n")]
        paragraphs[-1] = paragraphs[-1][:-1]
        return paragraphs

    @property
    def line_tokens_amount(self) -> int:
        token_size = self.font_width
        return (self.page_width - self.page_border_offset * 2) // token_size

    def convert_line(self, line, tokens, y, line_offset: int):
        x = self.page_border_offset
        for i, char in enumerate(line):
            begin = line_offset + i
            end = begin + 1
            offset = Offset(begin=begin, end=end)
            token = BadgerdocToken(
                bbox=[x, y, x + self.font_width, y + self.font_height],
                text=char,
                offset=offset,
            )
            tokens.append(token)
            x += self.font_width

    def calculate_page_size(
        self, tokens: List[BadgerdocToken], page_border_offset
    ) -> PageSize:
        return PageSize(
            width=max(t.bbox[2] for t in tokens) + page_border_offset,
            height=max(t.bbox[3] for t in tokens) + page_border_offset,
        )
