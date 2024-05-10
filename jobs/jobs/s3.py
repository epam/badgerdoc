import enum
from datetime import timedelta
from typing import Any, Dict, Literal, Optional, Union

from minio import Minio, credentials

from jobs import config
from jobs.logger import logger


class S3Providers(str, enum.Enum):
    MINIO = "minio"
    AWS_IAM = "aws_iam"
    AWS_ENV = "aws_env"
    AWS_CONF = "aws_config"


def get_minio_config(
    s3_provider: S3Providers,
    endpoint: Optional[str],
    access_key: Optional[str],
    secret_key: Optional[str],
    **kwargs: Optional[Union[str, bool]],
) -> Dict[str, Any]:
    minio_config = {"endpoint": endpoint, "secure": kwargs.get("secure")}
    if s3_provider == S3Providers.MINIO:
        minio_config["access_key"] = access_key
        minio_config["secret_key"] = secret_key
    elif s3_provider == S3Providers.AWS_IAM:
        minio_config["credentials"] = credentials.IamAwsProvider()
    elif s3_provider == S3Providers.AWS_ENV:
        minio_config["credentials"] = credentials.EnvAWSProvider()
    elif s3_provider == S3Providers.AWS_CONF:
        minio_config["credentials"] = credentials.AWSConfigProvider(
            profile=kwargs.get("aws_profile")
        )
    return minio_config


def get_minio_client() -> Minio:
    """Return Minio client if URI is provided via config.py."""
    s3_provider = S3Providers(config.S3_PROVIDER)
    logger.debug("S3_PROVIDER is set to %s", s3_provider)
    minio_config = get_minio_config(
        s3_provider=s3_provider,
        endpoint=config.S3_ENDPOINT,
        access_key=config.S3_ACCESS_KEY,
        secret_key=config.S3_SECRET_KEY,
        aws_profile=config.AWS_PROFILE,
        secure=config.MINIO_SECURE_CONNECTION,
    )
    return Minio(**minio_config)


def create_pre_signed_s3_url(
    bucket: str,
    path: str,
    method: Literal["GET"] = "GET",
    expires: timedelta = timedelta(days=config.S3_PRE_SIGNED_EXPIRES_DAYS),
    client: Minio = None,  # type: ignore
) -> str:
    if client is None:
        from .main import minio_client as client

    return client.get_presigned_url(
        method=method, bucket_name=bucket, object_name=path, expires=expires
    )
