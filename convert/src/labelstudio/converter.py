from typing import Optional

from src.badgerdoc.bd_annotation_model_practic import (
    BadgerdocAnnotation,
)
from src.badgerdoc.bd_tokens_model import Page
from src.badgerdoc.pdf_renderer import PDFRenderer
from src.labelstudio.annotation_converter import AnnotationConverter
from src.labelstudio.ls_models import LabelStudioModel
from src.plain_text.plain_text_converter import (
    TextToBadgerdocTokensConverter,
)


class Converter:
    def __init__(
        self,
    ) -> None:
        self.tokens_page: Optional[Page] = None
        self.badgerdoc_annotation: Optional[BadgerdocAnnotation] = None
        # self.pdf_renderer: Optional[PDFRenderer] = PDFRenderer()
        self.text_converter = TextToBadgerdocTokensConverter()

    # def to_badgerdoc(self, labelstudio_data: LabelStudioModel, pdf_path: Path):
    def to_badgerdoc(self, labelstudio_data: LabelStudioModel):
        # TODO: process several root elements
        self.tokens_page = self.text_converter.convert(
            labelstudio_data.__root__[0].data.text
        )

        # PDFRenderer().render_tokens(self.tokens_page.objs, pdf_path)
        # self.remove_non_printing_characters(self.tokens_page)

        annotation_converter = AnnotationConverter()
        self.badgerdoc_annotation = annotation_converter.convert(
            labelstudio_data, self.tokens_page
        )

    def remove_non_printing_characters(self, tokens_page: Page):
        pass
