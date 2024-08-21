from typing import Optional

from badgerdoc_storage import storage as bd_storage
from fastapi import APIRouter, Header, status

from convert.converters.pdf.pdf_to_badgerdoc_converter import (
    PDFToBadgerdocConverter,
)
from convert.models.pdf import PdfRequest

router = APIRouter(prefix="/pdf", tags=["pdf"])


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
)
def import_pdf(
    request: PdfRequest,
    x_current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> None:
    pdf_to_bd_use_case = PDFToBadgerdocConverter(
        bd_storage.get_storage(x_current_tenant)
    )
    pdf_to_bd_use_case.execute(
        s3_input_pdf=request.input_pdf,
        s3_output_tokens=request.output_tokens,
    )
