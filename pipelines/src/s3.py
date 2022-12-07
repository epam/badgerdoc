import enum
from typing import Any, Dict, Optional

from minio import Minio, credentials

from src import config, log

logger = log.get_logger(__file__)


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
    **kwargs: Optional[str],
) -> Dict[str, Any]:
    minio_config = {"endpoint": endpoint, "secure": False}
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
    s3_provider = S3Providers(config.S3_CREDENTIALS_PROVIDER)
    logger.debug("S3_CREDENTIALS_PROVIDER is set to %s", s3_provider)
    minio_config = get_minio_config(
        s3_provider=s3_provider,
        endpoint=config.S3_ENDPOINT,
        access_key=config.S3_ACCESS_KEY,
        secret_key=config.S3_SECRET_KEY,
        aws_profile=config.AWS_PROFILE,
    )
    return Minio(**minio_config)


def tenant_from_bucket(bucket: str) -> str:
    prefix = f"{config.S3_PREFIX}-" if config.S3_PREFIX else ""
    return bucket.replace(prefix, "", 1)
