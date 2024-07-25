import datetime
import logging
import os
from typing import Dict, List, Optional, Protocol
from urllib.parse import urlsplit

import azure.core.exceptions
import boto3
from azure.storage.blob import (
    BlobServiceClient,
    ContainerSasPermissions,
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

        # TODO: Check region

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
    logger.debug("S3 configured")
    return boto3_config


class BadgerDocStorageError(Exception):
    pass


class BadgerDocStorageResourceExistsError(BadgerDocStorageError):
    pass


class BadgerDocStorage(Protocol):
    def upload(
        self, target_path: str, file: str, content_type: Optional[str] = None
    ) -> None:
        pass

    def upload_obj(
        self, target_path: str, file: bytes, content_type: Optional[str] = None
    ) -> None:
        pass

    def exists(self, target_path: str) -> bool:
        pass

    def download(self, target_path: str, file: str) -> None:
        pass

    def gen_signed_url(self, file: str, exp: int) -> str:
        pass

    def list_objects(
        self, targe_path: str, recursive: bool = False
    ) -> List[str]:
        pass

    def remove(self, file: str) -> None:
        pass

    @property
    def tenant(self) -> str:
        pass


class BadgerDocS3Storage:
    def __init__(self, tenant: str) -> None:
        self._tenant = tenant
        self._bucket = self.__get_bucket_name()
        self.storage_configuration = create_boto3_config()
        self.s3_resource = boto3.resource("s3", **self.storage_configuration)

    @property
    def tenant(self) -> str:
        return self._tenant

    def __get_bucket_name(self) -> str:
        return f"{S3_PREFIX}-{self._tenant}" if S3_PREFIX else self._tenant

    def upload(
        self, target_path: str, file: str, content_type: Optional[str] = None
    ) -> None:
        bucket_name = self.__get_bucket_name()
        params = {"Filename": file, "Key": target_path}
        if content_type:
            params["ExtraArgs"] = {"ContentType": content_type}
        self.s3_resource.Bucket(bucket_name).upload_file(**params)

    def upload_obj(
        self, target_path: str, file: bytes, content_type: Optional[str] = None
    ) -> None:
        bucket_name = self.__get_bucket_name()
        params = {"Fileobj": file, "Key": target_path}
        if content_type:
            params["ExtraArgs"] = {"ContentType": content_type}
        self.s3_resource.Bucket(bucket_name).upload_fileobj(**params)

    def exists(self, target_path: str) -> bool:
        bucket_name = self.__get_bucket_name()
        try:
            self.s3_resource.Object(bucket_name, target_path).load()
            return True
        except ClientError as err:
            if err.response["Error"]["Code"] == "404":
                return False
            raise BadgerDocStorageError() from err

    def download(self, target_path: str, file: str) -> None:
        bucket_name = self.__get_bucket_name()
        try:
            self.s3_resource.Bucket(bucket_name).download_file(
                Key=target_path, Filename=file
            )
        except ClientError as err:
            raise BadgerDocStorageError(
                "Unable to download file: %s", target_path
            ) from err

    def gen_signed_url(self, file: str, exp: int) -> str:
        bucket_name = self.__get_bucket_name()
        signed_url = self.s3_resource.meta.client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket_name, "Key": file}
        )
        if STORAGE_PROVIDER == "MINIO" and MINIO_PUBLIC_HOST is not None:
            split = urlsplit(signed_url)
            new_url = f"{MINIO_PUBLIC_HOST}{split.path}"
            if split.query is not None:
                new_url += f"?{split.query}"
            return new_url

    def remove(self, file: str) -> None:
        pass


class BadgerDocAzureStorage:
    def __init__(self, tenant: str) -> None:
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
        with open(file, "rb") as data:
            blob_client.upload_blob(data)

    def upload_obj(
        self, target_path: str, file: bytes, content_type: Optional[str] = None
    ) -> None:
        try:
            blob_client = self.blob_service_client.get_blob_client(
                self._container_name, target_path
            )
            blob_client.upload_blob(file)
        except azure.core.exceptions.ResourceExistsError as err:
            raise BadgerDocStorageResourceExistsError() from err

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
            permission=ContainerSasPermissions(read=True),
            expiry=datetime.datetime.now() + datetime.timedelta(seconds=exp),
        )
        return blob_client.url + "?" + sas_token

    def list_objects(
        self, target_path: str, recursive: bool = False
    ) -> List[str]:
        if not recursive:
            target_path += "/"  # Append slash to get blobs only at top level.
        blob_iter = self.blob_service_client.list_blobs(
            self._container_name, name_starts_with=target_path
        )
        return [blob.name for blob in blob_iter]

    def remove(self, file: str) -> None:
        blob_client = self.blob_service_client.get_blob_client(
            self._container_name, file
        )
        blob_client.delete_blob()


def get_storage(tenant: str) -> BadgerDocStorage:
    if STORAGE_PROVIDER in S3_COMPATIBLE:
        return BadgerDocS3Storage(tenant)
    elif STORAGE_PROVIDER in AZURE_COMPATIBLE:
        return BadgerDocAzureStorage(tenant)
    else:
        raise BadgerDocStorageError(
            f"Engine {STORAGE_PROVIDER} is not supported"
        )
