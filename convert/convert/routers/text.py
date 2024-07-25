from typing import Optional

from badgerdoc_storage import storage as bd_storage
from fastapi import APIRouter, Header, status

from convert.converters.text.text_to_badgerdoc_converter import (
    TextToBadgerdocConverter,
)
from convert.models.text import TextRequest

router = APIRouter(prefix="/text", tags=["text"])


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
)
def import_text(
    request: TextRequest,
    x_current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> None:
    text_to_bd_use_case = TextToBadgerdocConverter(
        storage=bd_storage.get_storage(x_current_tenant),
    )
    text_to_bd_use_case.execute(
        s3_input_text=request.input_text,
        s3_output_pdf=request.output_pdf,
        s3_output_tokens=request.output_tokens,
    )
