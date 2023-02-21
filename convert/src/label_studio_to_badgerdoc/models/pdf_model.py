from pydantic import BaseModel

from src.label_studio_to_badgerdoc.models import S3Path


class PdfRequest(BaseModel):
    input_pdf: S3Path
    output_tokens: S3Path
