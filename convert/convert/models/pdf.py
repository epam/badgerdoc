from convert.models.common import S3Path
from pydantic import BaseModel


class PdfRequest(BaseModel):
    input_pdf: S3Path
    output_tokens: S3Path
