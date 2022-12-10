from collections import namedtuple
from typing import Any, Dict, List

from .models import BadgerdocToken, Offset, Page, PageSize

DEFAULT_PAGE_BORDER_OFFSET = 15


def generate_chunks(text: str, n=70) -> List[str]:
    return [text[i : i + n] for i in range(0, len(text), n)]


class PlainTextToBadgerdocTokenConverter:
    # TODO: calculate font width by font_height
    def __init__(
        self,
        page_width: int = 595,
        font_height: int = 11,
        font_width: int = 7,
        line_spacing: int = 2,
        page_border_offset: int = DEFAULT_PAGE_BORDER_OFFSET,
    ) -> None:

        self.page_width = page_width
        self.page_border_offset = page_border_offset
        self.font_height = font_height
        self.font_width = font_width
        self.line_spacing = line_spacing

    @property
    def amount_of_tokens_per_line(self) -> int:
        token_size = self.font_width
        return int(
            (self.page_width - self.page_border_offset * 2) / token_size
        )

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

    def _get_paragraphs(self, text: str) -> List[str]:
        paragraphs = [paragraph + "\n" for paragraph in text.split("\n")]
        paragraphs[-1] = paragraphs[-1][:-1]
        return paragraphs

    def calculate_page_size(
        self, tokens: List[BadgerdocToken], page_border_offset
    ) -> PageSize:
        return PageSize(
            width=max([t.bbox[2] for t in tokens]) + page_border_offset,
            height=max([t.bbox[3] for t in tokens]) + page_border_offset,
        )

    def convert(self, text: str) -> Page:
        paragraphs = self._get_paragraphs(text)

        tokens = []
        line_offset = 0
        y = self.page_border_offset
        for paragraph in paragraphs:
            lines = generate_chunks(paragraph, self.amount_of_tokens_per_line)
            for line in lines:
                self.convert_line(line, tokens, y, line_offset=line_offset)
                y += self.font_height * self.line_spacing
                line_offset += len(line)
            y += self.font_height

        page_size = self.calculate_page_size(tokens, self.page_border_offset)
        return Page(page_num=1, size=page_size, objs=tokens)
