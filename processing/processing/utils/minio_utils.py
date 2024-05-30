from minio import Minio
from minio.credentials import AWSConfigProvider, EnvAWSProvider, IamAwsProvider

from processing.config import settings
from processing.utils.logger import get_logger

logger = get_logger(__name__)


class NotConfiguredException(Exception):
    pass


def create_minio_config():
    minio_config = {}

    minio_config.update({"secure": settings.s3_secure})

    if settings.s3_endpoint:
        minio_config.update({"endpoint": settings.s3_endpoint})

    if settings.s3_provider == "minio":
        minio_config.update(
            {
                "access_key": settings.s3_access_key,
                "secret_key": settings.s3_secret_key,
            }
        )
    elif settings.s3_provider == "aws_iam":
        minio_config.update(
            {
                "credentials": IamAwsProvider(),
                "region": settings.aws_region,
                "access_key": settings.s3_access_key,
                "secret_key": settings.s3_secret_key,
            }
        )
    elif settings.s3_provider == "aws_env":
        minio_config.update({"credentials": EnvAWSProvider()})
    elif settings.s3_provider == "aws_config":
        # environmental variable AWS_PROFILE_NAME should be set
        minio_config.update(
            {
                "credentials": AWSConfigProvider(
                    profile=settings.aws_profile_name
                )
            }
        )
    else:
        raise NotConfiguredException(
            "s3 connection is not properly configured - "
            "s3_provider is not set"
        )
    logger.info(f"S3_Credentials provider - {settings.s3_provider}")

    return minio_config


class MinioCommunicator:
    client: Minio = None

    def __init__(self) -> None:
        if not MinioCommunicator.client:
            self.create_client()

    @classmethod
    def create_client(cls) -> None:
        minio_config = create_minio_config()
        cls.client = Minio(**minio_config)
        logger.info(
            "MinIO client for %s was created successfully",
            settings.s3_endpoint,
        )


def convert_bucket_name_if_s3prefix(bucket_name: str) -> str:
    if settings.s3_prefix:
        return f"{settings.s3_prefix}-{bucket_name}"
    else:
        return bucket_name
