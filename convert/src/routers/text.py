from fastapi import APIRouter, status

from src.config import minio_client
from src.label_studio_to_badgerdoc.models.text_model import TextRequest
from src.label_studio_to_badgerdoc.text_to_badgerdoc_use_case import TextToBDConvertUseCase

router = APIRouter(prefix="/text", tags=["text"])


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
)
def import_text(request: TextRequest) -> None:
    text_to_bd_use_case = TextToBDConvertUseCase(
        s3_client=minio_client,
    )
    text_to_bd_use_case.execute(
        s3_input_text=request.input_text,
        s3_output_pdf=request.output_pdf,
        s3_output_tokens=request.output_tokens,
    )
