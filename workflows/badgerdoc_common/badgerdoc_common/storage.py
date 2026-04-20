import logging
import os
from dataclasses import dataclass
from io import BytesIO

import aioboto3
from botocore.config import Config

logger = logging.getLogger(__name__)


@dataclass
class StorageWorkflowParams:
    workflow_package: str
    workflow_name: str
    workflow_id: str


def _build_storage_path(
    base_path: str, params: StorageWorkflowParams, file_path: str | list[str]
) -> str:
    path = f"{base_path}/{params.workflow_package}/{params.workflow_name}/{params.workflow_id}/"

    file_path = (
        file_path if isinstance(file_path, str) else "/".join(file_path)
    )
    path = f"{path}{file_path}"
    return path


def build_perm_path(
    params: StorageWorkflowParams, file_path: str | list[str]
) -> str:
    return _build_storage_path("data/workflows", params, file_path)


def build_temp_path(
    params: StorageWorkflowParams, file_path: str | list[str]
) -> str:
    return _build_storage_path("tmp/workflows", params, file_path)


def _get_s3_client():
    access_key = os.getenv("BADGERDOC_OBJECT_STORAGE_ACCESS_KEY")
    secret_key = os.getenv("BADGERDOC_OBJECT_STORAGE_SECRET_KEY")
    endpoint_url = os.getenv("BADGERDOC_OBJECT_STORAGE_URL")
    region_name = os.getenv("BADGERDOC_OBJECT_STORAGE_REGION", "us-east-1")
    addressing_style = os.getenv(
        "BADGERDOC_OBJECT_STORAGE_ADDRESSING_STYLE", "path"
    )

    config = Config(s3={"addressing_style": addressing_style})
    session = aioboto3.Session()
    return session.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint_url,
        region_name=region_name,
        config=config,
    )


async def badgerdoc_download(buffer: BytesIO, path: str) -> None:
    bucket_name = os.getenv("BADGERDOC_OBJECT_STORAGE_BUCKET")
    if not bucket_name:
        raise ValueError(
            "Bucket name is required. Set BADGERDOC_OBJECT_STORAGE_BUCKET "
            "environment variable"
        )

    buffer.seek(0)
    buffer.truncate(0)

    async with _get_s3_client() as s3_client:
        response = await s3_client.get_object(Bucket=bucket_name, Key=path)
        async for chunk in response["Body"]:
            buffer.write(chunk)

    buffer.seek(0)
    logger.info("Downloaded permanent file from: %s", path)


async def badgerdoc_download_temp(
    buffer: BytesIO, params: StorageWorkflowParams, file_path: str | list[str]
) -> None:
    return await badgerdoc_download(buffer, build_temp_path(params, file_path))


async def badgerdoc_download_perm(
    buffer: BytesIO, params: StorageWorkflowParams, file_path: str | list[str]
) -> None:
    return await badgerdoc_download(buffer, build_perm_path(params, file_path))


async def badgerdoc_store(buffer: BytesIO, path: str) -> str:
    bucket_name = os.getenv("BADGERDOC_OBJECT_STORAGE_BUCKET")
    if not bucket_name:
        raise ValueError(
            "Bucket name is required. Set BADGERDOC_OBJECT_STORAGE_BUCKET "
            "environment variable"
        )

    buffer.seek(0)
    async with _get_s3_client() as s3_client:
        await s3_client.put_object(
            Bucket=bucket_name, Key=path, Body=buffer.read()
        )

    logger.info("Uploaded file to: %s", path)
    logger.info("Stored temporary file at: %s", path)
    return path


async def badgerdoc_store_temp(
    buffer: BytesIO, params: StorageWorkflowParams, file_path: str | list[str]
) -> str:
    path = build_temp_path(params, file_path)
    await badgerdoc_store(buffer, path)
    return path


async def badgerdoc_store_perm(
    buffer: BytesIO, params: StorageWorkflowParams, file_path: str | list[str]
) -> str:
    path = build_perm_path(params, file_path)
    await badgerdoc_store(buffer, path)
    return path
