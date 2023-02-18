from typing import Any
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, BackgroundTasks, Depends, Header, status
from fastapi.responses import Response, StreamingResponse
from requests import HTTPError
from tenant_dependency import TenantData, get_tenant_info

from src.legacy.coco_export.convert import ConvertToCoco, ExportBadgerdoc
from src.legacy.coco_export.export_service import (
    export_run,
    export_run_and_return_url,
)
from src.legacy.coco_import.convert import ConvertToBadgerdoc
from src.legacy.coco_import.import_job import create_import_job
from src.config import minio_client, settings
from src.logger import get_logger
from src.legacy.models import coco
from src.legacy.utils.s3_utils import get_bucket_path

router = APIRouter(prefix="/coco", tags=["coco"])
LOGGER = get_logger(__file__)
tenant = get_tenant_info(
    url=settings.keycloak_url, algorithm="RS256", debug=True
)


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": coco.ImportJobCreatedSuccess},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": coco.UnavailableService,
        },
    },
)
def import_job_create(
    import_format: str,
    s3_data: coco.DataS3,
    current_tenant: str = Header(None, alias="X-Current-Tenant"),
    tenant_dependency: TenantData = Depends(tenant),
) -> Any:
    """Router gets dataset from s3, converts it to badgerdoc format"""
    import_formats = {"badgerdoc": ConvertToBadgerdoc}
    if import_format not in import_formats:
        LOGGER.error("Format not supported")
        return status.HTTP_404_NOT_FOUND
    try:
        job = create_import_job(
            import_format, s3_data, tenant_dependency, current_tenant
        )
        model = coco.ImportJobCreatedSuccess(
            job_id=job, msg=f"Import job {job} is created"
        )
        return {"message": model, "status": status.HTTP_201_CREATED}
    except HTTPError:
        return status.HTTP_500_INTERNAL_SERVER_ERROR


@router.post(
    "/export",
    status_code=200,
    responses={
        status.HTTP_201_CREATED: {
            "model": coco.ExportConvertStart,
            "description": "Conversion is started",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": coco.WrongConvertToCoco,
            "description": "Dataset not found",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": coco.UnavailableService,
            "description": "Service is unavailable",
        },
    },
)
def dataset_export(
    request: coco.ExportInputData,
    background: BackgroundTasks,
    token: TenantData = Depends(tenant),
    current_tenant: str = Header(None, alias="X-Current-Tenant"),
) -> Any:
    """
    Router get annotation by job_id, converts it to input format and returns
    the result as a zipfile
    """
    export_formats = {"coco": ConvertToCoco, "badgerdoc": ExportBadgerdoc}
    token = f"Bearer {token.__dict__.get('token', None)}"
    if request.export_format not in export_formats:
        LOGGER.error("Format not supported")
        return status.HTTP_404_NOT_FOUND
    try:
        url = export_run_and_return_url(
            request.job_lst,
            request.export_format,
            export_formats,
            background,
            current_tenant,
            token,
            validated_only=request.validated_only,
        )
        bucket, minio_path = get_bucket_path(url)
        return coco.ExportConvertStart(
            url=url,
            bucket=bucket,
            minio_path=minio_path,
            msg="Conversion is started",
        )
    except HTTPError:
        return status.HTTP_500_INTERNAL_SERVER_ERROR


@router.get(
    "/download",
    status_code=200,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": coco.WrongConvertToCoco,
            "description": "Dataset not found",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": coco.UnavailableService,
            "description": "Service is unavailable",
        },
    },
)
def download_dataset(
    url: str,
    background: BackgroundTasks,
    token: TenantData = Depends(tenant),
    current_tenant: str = Header(None, alias="X-Current-Tenant"),
) -> Any:
    response = requests.get(url)
    if response.status_code != 200:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    parsed = urlparse(url)
    minio_path = parsed.path[1:].split("/")
    bucket, key = minio_path[0], str.join("/", minio_path[1:-1])
    zip_file = minio_client.get_object(
        Bucket=bucket, Key=str.join("/", minio_path[1:])
    )
    background.add_task(
        minio_client.delete_object,
        Bucket=bucket,
        Key=str.join("/", minio_path[1:]),
    )
    return StreamingResponse(
        content=zip_file["Body"].iter_chunks(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=coco.zip"},
    )
