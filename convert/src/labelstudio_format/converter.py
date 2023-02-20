from pathlib import Path
from typing import Optional

from ..config import (
    DEFAULT_PAGE_BORDER_OFFSET,
    DEFAULT_PDF_FONT_HEIGHT,
    DEFAULT_PDF_FONT_WIDTH,
    DEFAULT_PDF_LINE_SPACING,
    DEFAULT_PDF_PAGE_WIDTH,
)
from src.badgerdoc_format.bd_annotation_model_practic import BadgerdocAnnotation
from src.badgerdoc_format.bd_tokens_model import Page
from src.labelstudio_format.ls_models import LabelStudioModel
from src.labelstudio_format.annotation_converter import AnnotationConverter
from src.badgerdoc_format.pdf_renderer import PDFRenderer
from src.plain_text_format.plain_text_converter import TextToBadgerdocTokensConverter


class Converter:
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

    def export_pdf(self, path: Path):
        if not self.pdf_renderer:
            return
        self.pdf_renderer.render_tokens(self.tokens_page.objs, path)
