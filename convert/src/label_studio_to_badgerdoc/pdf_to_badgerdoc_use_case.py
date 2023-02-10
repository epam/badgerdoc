import tempfile
from pathlib import Path

from src.label_studio_to_badgerdoc.badgerdoc_format.badgerdoc_format import (
    BadgerdocFormat,
)
from src.label_studio_to_badgerdoc.models import S3Path


class PDFToBDConvertUseCase:
    def __init__(self, s3_client) -> None:
        self.badgerdoc_format = BadgerdocFormat()
        self.s3_client = s3_client

    def execute(
        self,
        s3_input_pdf: S3Path,
        s3_output_tokens: S3Path,
    ) -> None:
        self.download_pdf_from_s3(s3_input_pdf)
        self.upload_badgerdoc_to_s3(
            s3_output_tokens,
        )

    def download_pdf_from_s3(self, s3_input_pdf: S3Path):
        with tempfile.TemporaryDirectory(dir="src") as tmp_dirname:
            tmp_dirname = Path(tmp_dirname)
            input_file = tmp_dirname / Path(s3_input_pdf.path).name
            self.s3_client.download_file(
                s3_input_pdf.bucket, s3_input_pdf.path, input_file
            )
            return self.badgerdoc_format.convert_from_pdf(input_file)

    def upload_badgerdoc_to_s3(self, s3_output_tokens) -> None:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dirname = Path(tmp_dirname)
            badgerdoc_tokens_path = tmp_dirname / Path("badgerdoc_tokens.json")
            self.badgerdoc_format.export_tokens(badgerdoc_tokens_path)
            self.s3_client.upload_file(
                str(badgerdoc_tokens_path),
                s3_output_tokens.bucket,
                s3_output_tokens.path,
            )
