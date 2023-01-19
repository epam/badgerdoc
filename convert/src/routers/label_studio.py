from fastapi import APIRouter, status

from src.config import minio_client
from src.label_studio_to_badegerdoc.badgerdoc_to_label_studio_use_case import (
    BDToLabelStudioConvertUseCase,
)
from src.label_studio_to_badegerdoc.models import LabelStudioRequest
from src.label_studio_to_badegerdoc.models.label_studio_models import BadgerdocToLabelStudioRequest
from src.label_studio_to_badegerdoc.label_studio_to_badgerdoc_use_case import (
    LabelStudioToBDConvertUseCase,
)

router = APIRouter(prefix="/label_studio", tags=["label_studio"])


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
)
def import_label_studio(request: LabelStudioRequest) -> None:
    label_studio_to_bd_use_case = LabelStudioToBDConvertUseCase(
        s3_client=minio_client,
    )
    label_studio_to_bd_use_case.execute(
        s3_input_annotation=request.input_annotation,
        s3_output_pdf=request.output_pdf,
        s3_output_tokens=request.output_tokens,
        s3_output_annotations=request.output_annotation,
    )


@router.post(
    "/export",
    status_code=status.HTTP_201_CREATED,
)
def export_label_studio(request: BadgerdocToLabelStudioRequest) -> None:
    bd_to_label_studio_use_case = BDToLabelStudioConvertUseCase(
        s3_client=minio_client,
    )
    bd_to_label_studio_use_case.execute(
        s3_input_tokens=request.input_tokens,
        s3_input_annotations=request.input_annotation,
        s3_output_annotation=request.output_annotation,
    )
