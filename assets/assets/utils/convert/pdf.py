import logging
import os
import tempfile
from pathlib import Path

from badgerdoc_storage import storage as bd_storage
from pydantic import BaseModel

from assets.utils.convert.badgerdoc import Badgerdoc
from assets.utils.convert.pdf_converter import (
    PlainPDFToBadgerdocTokensConverter,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class S3Path(BaseModel):
    bucket: str
    path: str


class PDFToBadgerdocConverter:

    def __init__(self, storage: bd_storage.BadgerDocStorage) -> None:
        self.badgerdoc_format = Badgerdoc()
        self.storage = storage

    def execute(
        self,
        s3_input_pdf: S3Path,
        s3_output_tokens: S3Path,
    ) -> None:
        self.download_pdf_from_s3(s3_input_pdf)
        self.upload_badgerdoc_to_s3(
            s3_output_tokens,
        )

    def download_pdf_from_s3(self, s3_input_pdf: str) -> None:
        logger.info("Converting from s3_input_pdf: %s", s3_input_pdf)
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)
            input_file = tmp_dir / "input.pdf"
            self.storage.download(s3_input_pdf, input_file)
            self.badgerdoc_format.tokens_pages = (
                PlainPDFToBadgerdocTokensConverter().convert(input_file)
            )

    def upload_badgerdoc_to_s3(self, s3_output_tokens: str) -> None:
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_dir = Path(tmp_dirname)
            badgerdoc_tokens_path = tmp_dir
            self.badgerdoc_format.export_tokens_to_folder(
                badgerdoc_tokens_path
            )
            s3_output_tokens_dir = os.path.dirname(s3_output_tokens)
            for file in Path.iterdir(tmp_dir):
                self.storage.upload(
                    target_path=s3_output_tokens_dir + f"/{file.name}",
                    file=str(badgerdoc_tokens_path) + f"/{file.name}",
                )
