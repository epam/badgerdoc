import collections
import string
from typing import Deque, List

from ...config import (
    DEFAULT_PAGE_BORDER_OFFSET,
    DEFAULT_PDF_FONT_HEIGHT,
    DEFAULT_PDF_FONT_WIDTH,
    DEFAULT_PDF_LINE_SPACING,
    DEFAULT_PDF_PAGE_WIDTH,
)
from ..models import BadgerdocToken, Offset, Page, PageSize


def generate_chunks(obj_to_split: List[str], size: int) -> List[List[str]]:
    return [
        obj_to_split[i : i + size] for i in range(0, len(obj_to_split), size)
    ]


class TextWrapper:
    """
    Split text to a separate lines. All whitespaces (including `\n`)
    recognized as a ` ` and require one place.
    """

    # textwrap.TextWrapper is not suitable, because we need to convert
    # it back to LabelStudio. Therefore, we need full control of process.

    def __init__(self, line_length: int) -> None:
        self.line_length = line_length

    def pop_beginning_whitespaces(self, text: Deque[str]) -> List[str]:
        wsp = []
        while text and text[0] in string.whitespace:
            wsp.append(text.popleft())
        return wsp

    def pop_next_word(self, text: Deque[str]) -> List[str]:
        word = []
        while text and text[0] not in string.whitespace:
            word.append(text.popleft())
        return word

    def wrap_paragraph(self, text: str) -> List[str]:
        chars = collections.deque(text)
        lines: List[List[str]] = []
        line: List[str] = self.pop_beginning_whitespaces(chars)

        while chars:
            if len(line) >= self.line_length:
                lines.append(line)
                line = []

            word = self.pop_next_word(chars)

            if len(word) + len(line) <= self.line_length:
                line.extend(word)
            else:
                if line:
                    lines.append(line)

                if len(word) <= self.line_length:
                    line = word
                else:
                    word_parts = generate_chunks(word, size=self.line_length)
                    line = word_parts.pop()
                    lines.extend(word_parts)

            line.extend(self.pop_beginning_whitespaces(chars))

        lines.append(line)
        return ["".join(line_) for line_ in lines]

    def wrap(self, text: str) -> List[str]:
        paragraphs = text.splitlines(keepends=True)
        lines = []
        for paragraph in paragraphs:
            lines.extend(self.wrap_paragraph(paragraph))
        return lines


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

        self.text_wrapper = TextWrapper(line_length=self.line_tokens_amount)

    def convert(self, text: str) -> Page:
        tokens = []
        line_offset = 0
        y = self.page_border_offset
        for line in self.text_wrapper.wrap(text):
            self.convert_line(line, tokens, y, line_offset=line_offset)
            y += self.font_height * self.line_spacing
            line_offset += len(line)
            if line.endswith("\n"):
                y += self.font_height

        page_size = self.calculate_page_size(tokens, self.page_border_offset)
        return Page(page_num=1, size=page_size, objs=tokens)

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
        if tokens:
            return PageSize(
                width=max(t.bbox[2] for t in tokens) + page_border_offset,
                height=max(t.bbox[3] for t in tokens) + page_border_offset,
            )
        return PageSize(
            width=page_border_offset,
            height=page_border_offset,
        )
