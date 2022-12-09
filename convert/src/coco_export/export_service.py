import os
import uuid
from typing import Any, Dict, List, Type
from zipfile import ZipFile

from fastapi import BackgroundTasks

from src.coco_export.convert import ConvertToCoco, ExportConvertBase
from src.config import minio_client
from src.logger import get_logger
from src.utils.s3_utils import convert_bucket_name_if_s3prefix

LOGGER = get_logger(__file__)


def export_run(
    job_lst: List[int],
    export_format: str,
    export_formats: Dict[str, Type[ExportConvertBase]],
    current_tenant: str,
    token: str,
    unique_identity: str,
    validated_only: bool = False,
) -> None:
    zip_file = ""
    for job_id in job_lst:
        converter = export_formats[export_format](
            job_id,
            current_tenant,
            token,
            unique_identity,
            export_format,
            validated_only=validated_only,
        )
        zip_file = converter.convert()  # type: ignore
    if export_format == "coco":
        with ZipFile(zip_file.filename, "a") as zip_obj:  # type: ignore
            zip_obj.write(f"{export_format}.json")
        os.remove(f"{export_format}.json")
    bucket_name = convert_bucket_name_if_s3prefix(current_tenant)
    minio_client.upload_file(
        zip_file.filename,  # type: ignore
        Bucket=bucket_name,
        Key=f"{export_format}/{unique_identity}.zip",
    )
    LOGGER.info(
        "zip archive was uploaded to bucket - %s, key - %s/%s.zip",
        bucket_name,
        export_format,
        unique_identity,
    )
    os.remove(zip_file.filename)  # type: ignore


def export_run_and_return_url(
    job_lst: List[int],
    export_format: str,
    export_formats: Dict[str, Type[ExportConvertBase]],
    background: BackgroundTasks,
    current_tenant: str,
    token: str,
    validated_only: bool = False,
) -> Any:
    unique_value = uuid.uuid4()
    bucket_name = convert_bucket_name_if_s3prefix(current_tenant)
    url = minio_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket_name,
            "Key": f"{export_format}/{unique_value}.zip",
        },
        ExpiresIn=3600,
        HttpMethod="GET",
    )

    background.add_task(
        export_run,
        job_lst,
        export_format,
        export_formats,
        current_tenant,
        token,
        unique_value,
        validated_only=validated_only,
    )
    return url
