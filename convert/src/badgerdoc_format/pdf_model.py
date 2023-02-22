from pydantic import BaseModel

from src.models.common import S3Path


class PdfRequest(BaseModel):
    input_pdf: S3Path
    output_tokens: S3Path
