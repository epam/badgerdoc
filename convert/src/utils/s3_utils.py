from pathlib import Path
from typing import Any, List, Optional, Tuple

import boto3
import urllib3
from fastapi import HTTPException, status

from src.config import minio_client, settings
from src.exceptions import BucketError, FileKeyError, UploadLimitExceedError
from src.logger import get_logger
from src.models import coco
from src.utils.common_utils import check_uploading_limit

logger = get_logger(__name__)


def convert_bucket_name_if_s3prefix(bucket_name: str) -> str:
    if settings.s3_prefix:
        return f"{settings.s3_prefix}-{bucket_name}"
    else:
        return bucket_name


class S3Manager:
    """
    Initializes boto3 client and boto3 resource objects with given credentials.
    """

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: Optional[str] = None,
    ) -> None:
        self.client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        self.resource = boto3.resource(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    def get_files(self, bucket_s3: str, files_keys: List[str]) -> None:
        """
        Downloads files from S3 storage
        """
        for file_key in files_keys:
            self.client.download_file(bucket_s3, file_key, Path(file_key).name)

    def _check_bucket_exist(self, bucket_s3: str) -> Any:
        """
        Checks if required bucket exists in S3
        """
        all_s3_buckets = [
            bucket.name for bucket in self.resource.buckets.all()
        ]
        if bucket_s3 not in all_s3_buckets:
            raise BucketError(f"bucket {bucket_s3} does not exist!")

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
                raise FileKeyError(f"file key {file_key} does not exist!")

    def check_s3(self, bucket_s3: str, files_keys: List[str]) -> Any:
        """
        Checks if required bucket and files are correct
        """
        try:
            self._check_bucket_exist(bucket_s3)
            self._check_files_exist(bucket_s3, files_keys)
        except FileKeyError as e:
            logger.error(f"S3 error - detail: {e}")
            raise FileKeyError(e)
        except BucketError as e:
            logger.error(f"S3 error - detail: {e}")
            raise BucketError(e)
        except urllib3.exceptions.MaxRetryError as e:
            logger.error(f"Connection error - detail: {e}")
            raise urllib3.exceptions.MaxRetryError


def s3_download_files(
    s3: S3Manager, bucket_s3: str, files_keys: List[str]
) -> None:
    """
    Tue function downloads list of the files from s3 storage
    Args:
        s3: S3Manager instance
        bucket_s3: s3 bucket name
        files_keys: list of the files for downloading
    """
    try:
        s3.check_s3(bucket_s3, files_keys)

    except (FileKeyError, BucketError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )

    except urllib3.exceptions.MaxRetryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    s3.get_files(bucket_s3, files_keys)


def download_file_from_aws(s3_data: coco.DataS3) -> S3Manager:
    """
    Establishes connect with s3 and downloads list of the files
    """
    try:
        check_uploading_limit(s3_data.files_keys)
    except UploadLimitExceedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    s3 = S3Manager(s3_data.aws_access_key_id, s3_data.aws_secret_access_key)
    s3_download_files(s3, s3_data.bucket_s3, s3_data.files_keys)
    return s3


def get_bucket_path(url: str) -> Tuple[str, str]:
    """Parse minio presigned url
    Args:
        url: minio presigned url
    Returns:
        Tuple bucket and path to file in minio
    """
    url = url.replace("http://minio/", "")
    url_paths = url.split("/")
    bucket, minio_path = url_paths[0], str.join("/", url_paths[1:])
    minio_path = minio_path.partition("?")[0]
    return bucket, minio_path
