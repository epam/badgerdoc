from pathlib import Path
from typing import Optional

from ..config import (
    DEFAULT_PAGE_BORDER_OFFSET,
    DEFAULT_PDF_FONT_HEIGHT,
    DEFAULT_PDF_FONT_WIDTH,
    DEFAULT_PDF_LINE_SPACING,
    DEFAULT_PDF_PAGE_WIDTH,
)
from .bd_annotation_model_practic import BadgerdocAnnotation
from .bd_tokens_model import Page
from .pdf_renderer import PDFRenderer


class BadgerdocFormat:
    def __init__(
        self,
        page_width=DEFAULT_PDF_PAGE_WIDTH,
        page_border_offset=DEFAULT_PAGE_BORDER_OFFSET,
        font_height=DEFAULT_PDF_FONT_HEIGHT,
        font_width=DEFAULT_PDF_FONT_WIDTH,
        line_spacing=DEFAULT_PDF_LINE_SPACING,
    ) -> None:
        self.page_width = page_width
        self.page_border_offset = page_border_offset
        self.font_height = font_height
        self.font_width = font_width
        self.line_spacing = line_spacing

        self.tokens_page: Optional[Page] = None
        self.badgerdoc_annotation: Optional[BadgerdocAnnotation] = None
        self.pdf_renderer: Optional[PDFRenderer] = PDFRenderer()

    def export_tokens(self, path: Path) -> None:
        if self.tokens_page:
            path.write_text(self.tokens_page.json(indent=4, by_alias=True))

    def export_annotations(self, path: Path):
        if self.badgerdoc_annotation:
            path.write_text(self.badgerdoc_annotation.json(indent=4))

    def export_pdf(self, path: Path):
        if not self.pdf_renderer:
            return
        self.pdf_renderer.render_tokens(self.tokens_page.objs, path)

    def import_tokens(self, path: Path):
        self.tokens_page = Page.parse_file(path)

    def import_annotations(self, path: Path):
        self.badgerdoc_annotation = BadgerdocAnnotation.parse_file(path)
