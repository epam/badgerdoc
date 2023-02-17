from io import BytesIO
from typing import Any, Dict, List, Optional

import boto3
import urllib3.exceptions

from assets import exceptions, logger
from assets.config import settings

logger_ = logger.get_logger(__name__)


class S3Manager:
    """
    Initializes boto3 client and boto3 resource objects with given credentials.
    """

    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        endpoint_url: Optional[str],
        region_name: str = None,
    ) -> None:
        self.client = boto3.client(
            "s3",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            endpoint_url=endpoint_url,
            region_name=region_name,
        )
        self.resource = boto3.resource(
            "s3",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            endpoint_url=endpoint_url,
            region_name=region_name,
        )

    def get_files(
        self, bucket_s3: str, files_keys: List[str]
    ) -> Dict[str, BytesIO]:
        """
        Downloads files from S3 storage
        """
        retrieved_objects = {}
        for file_key in files_keys:
            file_stream = BytesIO()
            self.client.download_fileobj(bucket_s3, file_key, file_stream)
            file_stream.seek(0)
            retrieved_objects[file_key] = file_stream
        return retrieved_objects

    def _check_bucket_exist(self, bucket_s3: str) -> Any:
        """
        Checks if required bucket exists in S3
        """
        all_s3_buckets = [
            bucket.name for bucket in self.resource.buckets.all()
        ]
        if bucket_s3 not in all_s3_buckets:
            raise exceptions.BucketError(f"bucket {bucket_s3} does not exist!")

    def _check_files_exist(self, bucket_s3: str, files_keys: List[str]) -> Any:
        """
        Checks if required file keys are correct
        """
        all_files_in_bucket = [
            content["Key"]
            for content in self.client.list_objects(Bucket=bucket_s3)[
                "Contents"
            ]
        ]
        for file_key in files_keys:
            if file_key not in all_files_in_bucket:
                raise exceptions.FileKeyError(
                    f"file key {file_key} does not exist!"
                )

    def check_s3(self, bucket_s3: str, files_keys: List[str]) -> Any:
        """
        Checks if required bucket and files are correct
        """
        try:
            self._check_bucket_exist(bucket_s3)
            self._check_files_exist(bucket_s3, files_keys)
        except (exceptions.FileKeyError, exceptions.FileKeyError) as e:
            logger_.exception(f"S3 error - detail: {e}")
            raise
        except urllib3.exceptions.MaxRetryError as e:
            logger_.exception(f"Connection error - detail: {e}")
            raise  # type: ignore


def get_bucket_name(tenant: str) -> str:
    return f"{settings.s3_prefix}-{tenant}" if settings.s3_prefix else tenant
