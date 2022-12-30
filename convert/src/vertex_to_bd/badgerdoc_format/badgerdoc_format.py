from pathlib import Path
from typing import Optional

from ..models.bd_tokens_model import Page
from ..models.vertex_models import LabelStudioModel
from .pdf_renderer import PDFRenderer
from .plain_text_converter import PlainTextToBadgerdocTokenConverter


class BadgerdocFormat:
    def __init__(
        self,
        page_width=595,
        page_border_offset=15,
        font_height=11,
        font_width=7,
        line_spacing=2,
    ) -> None:
        self.tokens_page: Optional[Page] = None
        self.pdf_renderer: PDFRenderer = PDFRenderer()
        self.text_converter = PlainTextToBadgerdocTokenConverter()

    def convert_from_labelstudio(self, labelstudio_data: LabelStudioModel):
        # TODO: process several root elements
        self.tokens_page = self.text_converter.convert(
            labelstudio_data.__root__[0].data.text
        )

    def export_tokens(self, path: Path):
        if self.tokens_page:
            path.write_text(self.tokens_page.json())

    def export_pdf(self, path: Path):
        self.pdf_renderer.render_tokens(self.tokens_page.objs, path)

    def import_tokens(self, path: Path):
        self.tokens_page = Page.parse_file(path)
