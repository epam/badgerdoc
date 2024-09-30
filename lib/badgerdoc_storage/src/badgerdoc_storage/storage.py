import datetime
import logging
import os
from typing import Any, Dict, List, Optional, Protocol
from urllib.parse import urlsplit

import boto3
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import (
    BlobServiceClient,
    ContainerSasPermissions,
    ContentSettings,
    generate_blob_sas,
)
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "").upper()

MINIO_PUBLIC_HOST = os.getenv("MINIO_PUBLIC_HOST")

S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_PREFIX = os.getenv("S3_PREFIX")
AZURE_BLOB_STORAGE_CONNECTION_STRING = os.getenv(
    "AZURE_BLOB_STORAGE_CONNECTION_STRING"
)

S3_COMPATIBLE = {"MINIO", "S3"}
AZURE_COMPATIBLE = {"AZURE"}


def create_boto3_config() -> Dict[str, Optional[str]]:
    logger.debug("Configure boto3 with %s", STORAGE_PROVIDER)
    boto3_config = {}
    if S3_ACCESS_KEY is not None:
        s3_secure = os.getenv("S3_SECURE", "").upper() == "TRUE"
        s3_endpoint = os.getenv("S3_ENDPOINT")
        boto3_config.update(
            {
                "aws_access_key_id": S3_ACCESS_KEY,
                "aws_secret_access_key": os.getenv("S3_SECRET_KEY"),
                "endpoint_url": (
                    (("https" if s3_secure else "http") + "://" + s3_endpoint)
                    if s3_endpoint
                    else None
                ),
            }
        )
        s3_region = os.getenv("S3_REGION")
        if s3_region:
            boto3_config["region_name"] = s3_region

    logger.debug("S3 configured")
    return boto3_config


class BadgerDocStorageError(Exception):
    pass


class BadgerDocStorage(Protocol):
    def upload(
        self, target_path: str, file: str, content_type: Optional[str] = None
    ) -> None:
        pass

    def upload_obj(
        self,
        target_path: str,
        file: bytes,
        content_type: Optional[str] = None,
    ) -> None:
        pass

    def exists(self, target_path: str) -> bool: ...

    def download(self, target_path: str, file: str) -> None: ...

    def gen_signed_url(self, file: str, exp: int) -> str: ...

    def list_objects(self, target_path: str) -> List[str]: ...

    def remove(self, file: str) -> None: ...

    def create_tenant_dir(self) -> bool: ...

    @property
    def tenant(self) -> str: ...


class BadgerDocS3Storage:
    def __init__(self, tenant: str) -> None:
        self._tenant = tenant
        self._bucket = self.__get_bucket_name()
        self.storage_configuration = create_boto3_config()
        logger.info("Storage configured: %s", self.storage_configuration)
        self.s3_resource = boto3.resource("s3", **self.storage_configuration)

    @property
    def tenant(self) -> str:
        return self._tenant

    def __get_bucket_name(self) -> str:
        return f"{S3_PREFIX}-{self._tenant}" if S3_PREFIX else self._tenant

    def upload(
        self, target_path: str, file: str, content_type: Optional[str] = None
    ) -> None:
        params: Dict[str, Any] = {"Filename": file, "Key": target_path}
        if content_type:
            params["ExtraArgs"] = {"ContentType": content_type}
        self.s3_resource.Bucket(self._bucket).upload_file(**params)

    def upload_obj(
        self,
        target_path: str,
        file: bytes,
        content_type: Optional[str] = None,
    ) -> None:
        params: Dict[str, Any] = {"Fileobj": file, "Key": target_path}
        if content_type:
            params["ExtraArgs"] = {"ContentType": content_type}
        self.s3_resource.Bucket(self._bucket).upload_fileobj(**params)

    def exists(self, target_path: str) -> bool:
        try:
            self.s3_resource.Object(self._bucket, target_path).load()
            return True
        except ClientError as err:
            if err.response["Error"]["Code"] == "404":
                return False
            raise BadgerDocStorageError() from err

    def download(self, target_path: str, file: str) -> None:
        try:
            self.s3_resource.Bucket(self._bucket).download_file(
                Key=target_path, Filename=file
            )
        except ClientError as err:
            raise BadgerDocStorageError(
                f"Unable to download file: {target_path}"
            ) from err

    def list_objects(self, target_path: str) -> List[str]:
        bucket = self.s3_resource.Bucket(self._bucket)
        objects = bucket.objects.filter(Prefix=target_path)
        return [obj.key for obj in objects]

    def gen_signed_url(self, file: str, exp: int) -> str:
        signed_url = self.s3_resource.meta.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": file},
            ExpiresIn=exp,
        )
        if STORAGE_PROVIDER == "MINIO" and MINIO_PUBLIC_HOST:
            split = urlsplit(signed_url)
            new_url = f"{MINIO_PUBLIC_HOST}{split.path}"
            if split.query is not None:
                new_url += f"?{split.query}"
            return new_url
        return signed_url

    def create_tenant_dir(self) -> bool:
        try:
            self.s3_resource.create_bucket(Bucket=self._bucket)
        except ClientError as err:
            if err.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
                # minio generates this response in case of bucket exists
                return False
            raise BadgerDocStorageError(
                "Unable to create or check tenant dir"
            ) from err
        return True

    def remove(self, file: str) -> None:
        raise NotImplementedError("Method not implemented")


class BadgerDocAzureStorage:
    def __init__(self, tenant: str) -> None:
        if AZURE_BLOB_STORAGE_CONNECTION_STRING is None:
            raise BadgerDocStorageError(
                "AZURE_BLOB_STORAGE_CONNECTION_STRING is not set."
            )
        self._container_name = tenant
        self._tenant = tenant
        self.blob_service_client = BlobServiceClient.from_connection_string(
            AZURE_BLOB_STORAGE_CONNECTION_STRING
        )

    @property
    def tenant(self) -> str:
        return self._tenant

    def upload(
        self, target_path: str, file: str, content_type: Optional[str] = None
    ) -> None:
        blob_client = self.blob_service_client.get_blob_client(
            self._container_name, target_path
        )
        if content_type:
            blob_headers = ContentSettings(content_type=content_type)
            blob_client.set_http_headers(blob_headers)
        with open(file, "rb") as data:
            blob_client.upload_blob(data)

    def upload_obj(
        self,
        target_path: str,
        file: bytes,
        content_type: Optional[str] = None,
    ) -> None:
        try:
            blob_client = self.blob_service_client.get_blob_client(
                self._container_name, target_path
            )
            blob_client.upload_blob(file, overwrite=True)
            if content_type:
                blob_headers = ContentSettings(content_type=content_type)
                blob_client.set_http_headers(blob_headers)
        except Exception as err:
            raise BadgerDocStorageError(
                f"Unable to upload file into {target_path}"
            ) from err

    def exists(self, target_path: str) -> bool:
        blob_client = self.blob_service_client.get_blob_client(
            self._container_name, target_path
        )
        return blob_client.exists()

    def download(self, target_path: str, file: str) -> None:
        blob_client = self.blob_service_client.get_blob_client(
            self._container_name, target_path
        )
        with open(file, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())

    def gen_signed_url(self, file: str, exp: int) -> str:
        blob_client = self.blob_service_client.get_blob_client(
            self._container_name, file
        )
        sas_token = generate_blob_sas(
            blob_client.account_name,
            blob_client.container_name,
            blob_client.blob_name,
            snapshot=blob_client.snapshot,
            account_key=blob_client.credential.account_key,
            permission=ContainerSasPermissions(read=True),  # type: ignore
            expiry=datetime.datetime.now() + datetime.timedelta(minutes=exp),
        )
        return blob_client.url + "?" + sas_token

    def list_objects(self, target_path: str) -> List[str]:
        if not target_path.endswith("/"):
            target_path += "/"
        container_client = self.blob_service_client.get_container_client(
            self._tenant
        )
        blob_iter = container_client.walk_blobs(name_starts_with=target_path)
        return [blob.name for blob in blob_iter]

    def create_tenant_dir(self) -> bool:
        try:
            self.blob_service_client.create_container(self._container_name)
            return True
        except ResourceExistsError:
            return False

    def remove(self, file: str) -> None:
        blob_client = self.blob_service_client.get_blob_client(
            self._container_name, file
        )
        blob_client.delete_blob()


def get_storage(tenant: str) -> BadgerDocStorage:
    if STORAGE_PROVIDER in S3_COMPATIBLE:
        return BadgerDocS3Storage(tenant)
    if STORAGE_PROVIDER in AZURE_COMPATIBLE:
        return BadgerDocAzureStorage(tenant)
    raise BadgerDocStorageError(f"Engine {STORAGE_PROVIDER} is not supported")
