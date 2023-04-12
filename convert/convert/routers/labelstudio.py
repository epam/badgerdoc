from typing import Optional

from convert.config import minio_client, settings
from convert.converters.labelstudio.badgerdoc_to_labelstudio_converter import (
    BadgerdocToLabelstudioConverter,
)
from convert.converters.labelstudio.labelstudio_to_badgerdoc_converter import (
    LabelstudioToBadgerdocConverter,
)
from convert.converters.labelstudio.wip_badgerdoc_to_labelstudio_converter import (
    WipBadgerdocToLabelstudioConverter,
)

from convert.models.labelstudio import (
    BadgerdocToLabelStudioRequest,
    LabelStudioRequest,
    WipBadgerdocToLabelStudioRequest,
)
from fastapi import APIRouter, Depends, Header, status
from tenant_dependency import TenantData, get_tenant_info

router = APIRouter(prefix="/labelstudio", tags=["labelstudio"])
tenant = get_tenant_info(
    url=settings.keycloak_url, algorithm="RS256", debug=True
)


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
)
def import_labelstudio(
    request: LabelStudioRequest,
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    token_data: TenantData = Depends(tenant),
) -> None:
    labelstudio_to_bd_use_case = LabelstudioToBadgerdocConverter(
        s3_client=minio_client,
        current_tenant=current_tenant,
        token_data=token_data,
        s3_input_annotation=request.input_annotation,
        s3_output_bucket=request.output_bucket,
        validation_type=request.validation_type,
        deadline=request.deadline,
        extensive_coverage=request.extensive_coverage,
        annotators=request.annotators,
        validators=request.validators,
    )
    labelstudio_to_bd_use_case.execute()


@router.post(
    "/export",
    status_code=status.HTTP_201_CREATED,
)
def export_labelstudio(
    request: BadgerdocToLabelStudioRequest,
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    token_data: TenantData = Depends(tenant),
) -> None:
    bd_to_labelstudio_use_case = BadgerdocToLabelstudioConverter(
        s3_client=minio_client,
        current_tenant=current_tenant,
        token_data=token_data,
    )
    bd_to_labelstudio_use_case.execute(
        s3_input_tokens=request.input_tokens,
        s3_input_annotations=request.input_annotation,
        s3_input_manifest=request.input_manifest,
        s3_output_annotation=request.output_annotation,
    )


@router.post(
    "/wip_export",
    status_code=status.HTTP_201_CREATED,
)
def export_labelstudio(
    request: WipBadgerdocToLabelStudioRequest,
    current_tenant: str = Header(None, alias="X-Current-Tenant"),
    token_data: TenantData = Depends(tenant),
) -> None:
    bd_to_labelstudio_converter = WipBadgerdocToLabelstudioConverter(
        s3_client=minio_client,
        current_tenant=current_tenant,
        token_data=token_data
    )
    bd_to_labelstudio_converter.execute(
        s3_input_tokens=request.input_tokens,
        s3_input_manifest=request.input_manifest,
        s3_output_annotation=request.output_annotation,
    )
