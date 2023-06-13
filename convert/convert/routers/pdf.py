import datetime

from fastapi import APIRouter, status

from convert.config import minio_client
from convert.converters.pdf.pdf_to_badgerdoc_converter import (
    PDFToBadgerdocConverter,
)
from convert.models.pdf import PdfRequest, PDFResponse

router = APIRouter(prefix="/pdf", tags=["pdf"])


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
)
def import_pdf(request: PdfRequest) -> PDFResponse:
    before = datetime.datetime.now()
    pdf_to_bd_use_case = PDFToBadgerdocConverter(
        s3_client=minio_client,
    )
    pdf_to_bd_use_case.execute(
        s3_input_pdf=request.input_pdf,
        s3_output_tokens=request.output_tokens,
    )
    return PDFResponse(
        runtime=f"runtime: {str(datetime.datetime.now() - before)}"
    )
