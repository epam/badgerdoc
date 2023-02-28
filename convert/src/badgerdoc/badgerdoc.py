from pathlib import Path
from typing import Optional

from src.pdf.pdf_converter import PlainPDFToBadgerdocTokensConverter

from .bd_annotation_model_practic import BadgerdocAnnotation
from .bd_tokens_model import BadgerdocToken, Page
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
            path.write_text(
                self.tokens_page.json(by_alias=True, exclude_none=True)
            )

    def export_annotations(self, path: Path) -> None:
        if self.badgerdoc_annotation:
            path.write_text(
                self.badgerdoc_annotation.json(indent=4, exclude_none=True)
            )

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

    def remove_non_printing_tokens(self):
        if not self.tokens_page:
            return
        if not isinstance(self.tokens_page, Page):
            return

        needed_objs = []
        is_start_string = True
        non_printable_sequence = []
        for token_obj in self.tokens_page.objs:
            char = token_obj.text
            if char.isspace() and is_start_string:
                non_printable_sequence.append(char)
                continue
            if not char.isspace():
                is_start_string = False
                copy_of_obj = token_obj.copy()
                needed_objs.append(copy_of_obj)
                if non_printable_sequence:
                    needed_objs[0].previous = "".join(non_printable_sequence)
                continue
            if char.isspace():
                previous_text = needed_objs[-1].after
                needed_objs[-1].after = (
                    char if not previous_text else previous_text + char
                )

        self.tokens_page.objs = needed_objs
