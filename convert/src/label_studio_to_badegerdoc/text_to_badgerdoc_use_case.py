import tempfile
from pathlib import Path

from ..config import DEFAULT_PAGE_BORDER_OFFSET
from .badgerdoc_format.badgerdoc_format import BadgerdocFormat
from .badgerdoc_format.pdf_renderer import PDFRenderer
from .badgerdoc_format.plain_text_converter import (
    TextToBadgerdocTokensConverter,
)
from .models.common import S3Path


class TextToBDConvertUseCase:
    def __init__(
        self,
        s3_client,
    ) -> None:
        page_border_offset = DEFAULT_PAGE_BORDER_OFFSET
        self.plain_text_converter = TextToBadgerdocTokensConverter(
            page_border_offset=page_border_offset
        )
        self.pdf_renderer = PDFRenderer(page_border_offset=page_border_offset)

        self.badgerdoc_format = BadgerdocFormat()
        self.s3_client = s3_client

    def execute(
        self,
        s3_input_text: S3Path,
        s3_output_pdf: S3Path,
        s3_output_tokens: S3Path,
    ) -> None:
        text = self.download_text_from_s3(s3_input_text)
        self.badgerdoc_format.convert_from_text(text)
        self.upload_badgerdoc_to_s3(
            s3_output_tokens,
            s3_output_pdf,
        )

    def download_text_from_s3(
        self,
        s3_input_text: S3Path,
    ) -> str:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dirname = Path(tmp_dirname)
            input_file = tmp_dirname / Path(s3_input_text.path).name

            self.s3_client.download_file(
                s3_input_text.bucket,
                s3_input_text.path,
                str(input_file),
            )
            return input_file.read_text()

    def upload_badgerdoc_to_s3(
        self,
        s3_output_tokens,
        s3_output_pdf,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dirname = Path(tmp_dirname)

            badgerdoc_tokens_path = tmp_dirname / Path("badgerdoc_tokens.json")
            self.badgerdoc_format.export_tokens(badgerdoc_tokens_path)
            self.s3_client.upload_file(
                str(badgerdoc_tokens_path),
                s3_output_tokens.bucket,
                s3_output_tokens.path,
            )

            pdf_path = tmp_dirname / Path("badgerdoc_render.pdf")
            self.badgerdoc_format.export_pdf(pdf_path)
            self.s3_client.upload_file(
                str(pdf_path), s3_output_pdf.bucket, s3_output_pdf.path
            )
