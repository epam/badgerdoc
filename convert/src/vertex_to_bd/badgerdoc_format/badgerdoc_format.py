from pathlib import Path
from typing import Optional

from ...config import (
    DEFAULT_PAGE_BORDER_OFFSET,
    DEFAULT_PDF_FONT_HEIGHT,
    DEFAULT_PDF_FONT_WIDTH,
    DEFAULT_PDF_LINE_SPACING,
    DEFAULT_PDF_PAGE_WIDTH,
)
from ..models.bd_annotation_model import BadgerdocAnnotation
from ..models.bd_tokens_model import Page
from ..models.vertex_models import LabelStudioModel
from .annotation_converter import AnnotationConverter
from .pdf_renderer import PDFRenderer
from .plain_text_converter import TextToBadgerdocTokensConverter


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
        self.text_converter = TextToBadgerdocTokensConverter()

    def convert_from_labelstudio(self, labelstudio_data: LabelStudioModel):
        # TODO: process several root elements
        self.tokens_page = self.text_converter.convert(
            labelstudio_data.__root__[0].data.text
        )
        annotation_converter = AnnotationConverter()
        self.badgerdoc_annotation = annotation_converter.convert(
            labelstudio_data, self.tokens_page
        )

    def convert_from_text(self, text: str):
        self.tokens_page = self.text_converter.convert(text)

    def export_tokens(self, path: Path):
        if self.tokens_page:
            path.write_text(self.tokens_page.json(indent=4))

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
