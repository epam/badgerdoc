from io import BytesIO
from typing import Any, Dict

from pypdf import PdfReader

from lib.spark_helper.storage_service import SparkStorageService


def extract_text_from_pdf(pdf_content: bytes) -> str:

    reader = PdfReader(BytesIO(pdf_content))
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    return text


class FilesStorage:
    VOLUME_NAME = "files"
    TXT_STORAGE_PATH = VOLUME_NAME + "/{file_id}/{file_id}.txt"
    PDF_STORAGE_PATH = VOLUME_NAME + "/{file_id}/{file_id}.pdf"

    def __init__(self, configs: Dict[str, Any]) -> None:
        self.storage_service = SparkStorageService(configs)
        self.storage_service.create_volume_if_not_exists(self.VOLUME_NAME)

    def store_pdf(self, pdf_content: bytes, file_id: int) -> str:

        pdf_file_path = self.PDF_STORAGE_PATH.format(file_id=file_id)
        self.storage_service.write_binary(pdf_content, pdf_file_path)

        return pdf_file_path

    def store_text(self, pdf_content: bytes, file_id: int) -> str:

        pdf_text = extract_text_from_pdf(pdf_content)

        txt_file_path = self.TXT_STORAGE_PATH.format(file_id=file_id)
        self.storage_service.write_text(pdf_text, txt_file_path)

        return txt_file_path
