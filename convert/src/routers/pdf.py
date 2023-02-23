from fastapi import APIRouter, status

from src.config import minio_client
from src.label_studio_to_badgerdoc.models.pdf_model import PdfRequest
from src.label_studio_to_badgerdoc.pdf_to_badgerdoc_use_case import (
    PDFToBDConvertUseCase,
)

router = APIRouter(prefix="/pdf", tags=["pdf"])


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
)
def import_pdf(request: PdfRequest) -> None:
    pdf_to_bd_use_case = PDFToBDConvertUseCase(
        s3_client=minio_client,
    )
    pdf_to_bd_use_case.execute(
        s3_input_pdf=request.input_pdf,
        s3_output_tokens=request.output_tokens,
    )
