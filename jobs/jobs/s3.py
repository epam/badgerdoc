import enum
import logging
from typing import Dict, Literal, Optional

import aioboto3

from jobs import config

logger = logging.getLogger(__name__)


class S3Providers(str, enum.Enum):
    MINIO = "minio"
    AWS_IAM = "aws_iam"
    AWS_ENV = "aws_env"
    AWS_CONF = "aws_config"


class NotConfiguredException(Exception):
    pass


def create_boto3_config() -> Dict[str, Optional[str]]:
    boto3_config = {}
    if config.S3_PROVIDER == S3Providers.MINIO:
        boto3_config.update(
            {
                "aws_access_key_id": config.S3_ACCESS_KEY,
                "aws_secret_access_key": config.S3_SECRET_KEY,
                "endpoint_url": f"http://{config.S3_ENDPOINT}",
            }
        )
    elif config.S3_PROVIDER == S3Providers.AWS_IAM:
        # No additional updates to config needed - boto3 uses env vars
        ...
    else:
        raise NotConfiguredException(
            "s3 connection is not properly configured - "
            "s3_credentials_provider is not set"
        )
    logger.info(f"S3_Credentials provider - {config.S3_PROVIDER}")
    return boto3_config


def s3_resource():
    boto_config = create_boto3_config()
    # local is a stub for minio provider, check create_boto3_config
    session = aioboto3.Session()
    return session.resource("s3", **boto_config)


async def create_pre_signed_s3_url(
    bucket: str,
    path: str,
    action: Literal["get_object"] = "get_object",
    expire_in_hours: int = config.S3_PRE_SIGNED_EXPIRES_HOURS,
) -> str:
    async with s3_resource() as resource:
        client = resource.meta.client
        return await client.generate_presigned_url(
            action,
            Params={"Bucket": bucket, "Key": path},
            ExpiresIn=expire_in_hours * 60 * 60,
        )
