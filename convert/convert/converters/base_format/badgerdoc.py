from pathlib import Path
from typing import List, Optional

from convert.converters.utils import filter_printing_tokens

from .models.annotation_practic import BadgerdocAnnotation
from .models.tokens import Page
from .pdf_renderer import PDFRenderer


class Badgerdoc:
    def __init__(
        self,
    ) -> None:
        self.tokens_page: Optional[Page] = None
        self.tokens_pages: Optional[List[Page]] = None
        self.badgerdoc_annotation: Optional[BadgerdocAnnotation] = None
        self.pdf_renderer: Optional[PDFRenderer] = PDFRenderer()

    def export_tokens_to_folder(self, tokens_path: Path) -> None:
        if self.tokens_pages:
            for i, page in enumerate(self.tokens_pages, start=1):
                page_file = tokens_path / Path(f"{i}.json")
                page_file.write_text(page.json(by_alias=True))

    def export_tokens(self, path: Path) -> None:
        if self.tokens_page:
            path.write_text(
                self.tokens_page.json(by_alias=True, exclude_none=True)
            )

    def export_annotations(self, path: Path) -> None:
        if self.badgerdoc_annotation:
            path.write_text(
                self.badgerdoc_annotation.json(indent=4, exclude_none=True)
            )

    def export_pdf(self, path: Path) -> None:
        if not self.pdf_renderer or not self.tokens_page:
            return
        self.pdf_renderer.render_tokens(self.tokens_page.objs, path)

    def import_tokens(self, path: Path) -> None:
        self.tokens_page = Page.parse_file(path)

    def import_annotations(self, path: Path) -> None:
        self.badgerdoc_annotation = BadgerdocAnnotation.parse_file(path)

    def remove_non_printing_tokens(self) -> None:
        if self.tokens_page:
            self.tokens_page.objs = filter_printing_tokens(
                self.tokens_page.objs
            )
