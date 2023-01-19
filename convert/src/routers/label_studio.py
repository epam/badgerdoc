from fastapi import APIRouter

from src.label_studio_to_badgerdoc.badgerdoc_to_label_studio_use_case import (
    BDToLabelStudioConvertUseCase,
)
from src.label_studio_to_badgerdoc.models import LabelStudioRequest
from src.label_studio_to_badgerdoc.models.label_studio_models import BadgerdocToLabelStudioRequest
from src.label_studio_to_badgerdoc.label_studio_to_badgerdoc_use_case import (
    LabelStudioToBDConvertUseCase,
)
from src.config import minio_client, settings
from tenant_dependency import TenantData, get_tenant_info
from typing import Optional
from fastapi import Depends, Header, status

router = APIRouter(prefix="/label_studio", tags=["label_studio"])
tenant = get_tenant_info(
    url=settings.keycloak_url, algorithm="RS256", debug=True
)


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
)
def import_label_studio(
    request: LabelStudioRequest,
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    token_data: TenantData = Depends(tenant),
) -> None:
    label_studio_to_bd_use_case = LabelStudioToBDConvertUseCase(
        s3_client=minio_client,
        current_tenant=current_tenant,
        token_data=token_data,
        s3_input_annotation=request.input_annotation,
        s3_output_bucket=request.output_bucket,
        s3_output_file_id=request.output_file_id
    )
    label_studio_to_bd_use_case.execute()


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
