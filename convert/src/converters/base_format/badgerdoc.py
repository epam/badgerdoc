from pathlib import Path
from typing import Optional

from src.converters.pdf.pdf_converter import PlainPDFToBadgerdocTokensConverter

from .models.annotation_practic import BadgerdocAnnotation
from .models.tokens import Page
from .pdf_renderer import PDFRenderer


class Badgerdoc:
    def __init__(
        self,
    ) -> None:
        self.tokens_page: Optional[Page] = None
        self.badgerdoc_annotation: Optional[BadgerdocAnnotation] = None
        self.pdf_renderer: Optional[PDFRenderer] = PDFRenderer()
        self.pdf_converter = PlainPDFToBadgerdocTokensConverter()

    def export_tokens_to_folder(self, tokens_path: Path) -> None:
        if self.tokens_page:
            for i, part in enumerate(self.tokens_page, start=1):
                path_file = tokens_path / Path(f"{i}.json")
                path_file.write_text(part.json(by_alias=True))

    def export_tokens(self, path: Path) -> None:
        if self.tokens_page:
            path.write_text(self.tokens_page.json(by_alias=True))

    def export_annotations(self, path: Path) -> None:
        if self.badgerdoc_annotation:
            path.write_text(self.badgerdoc_annotation.json(indent=4))

    def export_pdf(self, path: Path) -> None:
        if not self.pdf_renderer:
            return
        self.pdf_renderer.render_tokens(self.tokens_page.objs, path)

    def import_tokens(self, path: Path) -> None:
        self.tokens_page = Page.parse_file(path)

    def import_annotations(self, path: Path) -> None:
        self.badgerdoc_annotation = BadgerdocAnnotation.parse_file(path)

    def convert_from_pdf(self, pdf) -> None:
        self.tokens_page = self.pdf_converter.convert(pdf)
