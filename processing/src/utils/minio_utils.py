from minio import Minio
from minio.credentials import AWSConfigProvider, EnvAWSProvider, IamAwsProvider

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NotConfiguredException(Exception):
    pass


def create_minio_config():
    minio_config = {}

    minio_config.update({"secure": settings.minio_secure_connection})

    if settings.minio_server:
        minio_config.update({"endpoint": settings.minio_server})

    if settings.s3_credentials_provider == "minio":
        minio_config.update(
            {
                "access_key": settings.minio_root_user,
                "secret_key": settings.minio_root_password,
            }
        )
    elif settings.s3_credentials_provider == "aws_iam":
        minio_config.update({"credentials": IamAwsProvider()})
    elif settings.s3_credentials_provider == "aws_env":
        minio_config.update({"credentials": EnvAWSProvider()})
    elif settings.s3_credentials_provider == "aws_config":
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
            "s3_credentials_provider is not set"
        )
    logger.info(
        f"S3_Credentials provider - {settings.s3_credentials_provider}"
    )

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
            settings.minio_server,
        )


def convert_bucket_name_if_s3prefix(bucket_name: str) -> str:
    if settings.s3_prefix:
        return f"{settings.s3_prefix}-{bucket_name}"
    else:
        return bucket_name
