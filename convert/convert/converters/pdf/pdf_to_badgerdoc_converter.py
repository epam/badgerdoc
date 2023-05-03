import os
import tempfile
from pathlib import Path

from botocore.client import BaseClient

from convert.converters.base_format.badgerdoc import Badgerdoc
from convert.converters.pdf.pdf_converter import (
    PlainPDFToBadgerdocTokensConverter,
)
from convert.models.common import S3Path


class PDFToBadgerdocConverter:
    badgerdoc_format = Badgerdoc()

    def __init__(self, s3_client: BaseClient) -> None:
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

    def download_pdf_from_s3(self, s3_input_pdf: S3Path) -> None:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)
            input_file = tmp_dir / Path(s3_input_pdf.path).name
            self.s3_client.download_file(
                s3_input_pdf.bucket, s3_input_pdf.path, input_file
            )
            self.badgerdoc_format.tokens_pages = (
                PlainPDFToBadgerdocTokensConverter().convert(input_file)
            )

    def upload_badgerdoc_to_s3(self, s3_output_tokens: S3Path) -> None:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)
            badgerdoc_tokens_path = tmp_dir
            self.badgerdoc_format.export_tokens_to_folder(
                badgerdoc_tokens_path
            )
            s3_output_tokens_dir = os.path.dirname(Path(s3_output_tokens.path))
            for file in Path.iterdir(tmp_dir):
                self.s3_client.upload_file(
                    str(badgerdoc_tokens_path) + f"/{file.name}",
                    s3_output_tokens.bucket,
                    s3_output_tokens_dir + f"/{file.name}",
                )
