import tempfile
from pathlib import Path

from badgerdoc_storage import storage as bd_storage

from convert.config import DEFAULT_PAGE_BORDER_OFFSET
from convert.converters.base_format.badgerdoc import Badgerdoc
from convert.converters.base_format.pdf_renderer import PDFRenderer
from convert.converters.text.text_to_tokens_converter import (
    TextToBadgerdocTokensConverter,
)
from convert.models.common import S3Path


class TextToBadgerdocConverter:
    def __init__(
        self,
        storage: bd_storage.BadgerDocStorage,
    ) -> None:
        page_border_offset = DEFAULT_PAGE_BORDER_OFFSET
        self.plain_text_converter = TextToBadgerdocTokensConverter(
            page_border_offset=page_border_offset
        )
        self.pdf_renderer = PDFRenderer(page_border_offset=page_border_offset)

        self.badgerdoc_format = Badgerdoc()
        self.storage = storage

    def execute(
        self,
        s3_input_text: S3Path,
        s3_output_pdf: S3Path,
        s3_output_tokens: S3Path,
    ) -> None:
        text = self.download(s3_input_text)
        self.badgerdoc_format.tokens_page = self.plain_text_converter.convert(
            text
        )
        self.upload(
            s3_output_tokens,
            s3_output_pdf,
        )

    def download(
        self,
        s3_input_text: S3Path,
    ) -> str:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)
            input_file = tmp_dir / Path(s3_input_text.path).name

            self.storage.download(
                target_path=s3_input_text.path,
                file=str(input_file),
            )
            return input_file.read_text()

    def upload(
        self,
        s3_output_tokens: S3Path,
        s3_output_pdf: S3Path,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)

            badgerdoc_tokens_path = tmp_dir / Path("badgerdoc_tokens.json")
            self.badgerdoc_format.export_tokens(badgerdoc_tokens_path)
            self.storage.upload(
                target_path=s3_output_tokens.path,
                file=str(badgerdoc_tokens_path),
            )

            pdf_path = tmp_dirname / Path("badgerdoc_render.pdf")
            self.badgerdoc_format.export_pdf(pdf_path)
            self.storage.upload(
                target_path=s3_output_pdf.path, file=str(pdf_path)
            )
