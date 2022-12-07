import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import boto3
from botocore.client import BaseClient
from mypy_extensions import KwArg, VarArg
from pydantic import BaseSettings, Field
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from src import logger

logger_ = logger.get_logger(__name__)


class Settings(BaseSettings):
    """Base settings values"""

    minio_host: Optional[str] = os.getenv("MINIO_HOST")
    minio_access_key: Optional[str] = os.getenv("MINIO_ACCESS_KEY")
    minio_secret_key: Optional[str] = os.getenv("MINIO_SECRET_KEY")
    s3_prefix: Optional[str] = os.getenv("S3_PREFIX")
    s3_credentials_provider: Optional[str] = os.getenv(
        "S3_CREDENTIALS_PROVIDER", "minio"
    )
    uploading_limit: int = Field(100, env="UPLOADING_LIMIT")
    coco_image_format: str = "jpg"
    dpi: int = 300
    root_path: Optional[str] = os.getenv("ROOT_PATH")
    assets_service_url: Optional[str] = os.getenv("ASSETS_SERVICE_URL")
    category_service_url: Optional[str] = os.getenv("CATEGORY_SERVICE_URL")
    import_coco_url: Optional[str] = os.getenv("IMPORT_COCO_URL")
    job_service_url: Optional[str] = os.getenv("JOB_SERVICE_URL")
    annotation_service_url: Optional[str] = os.getenv("ANNOTATION_SERVICE_URL")
    keycloak_url: Optional[str] = os.getenv("KEYCLOAK_URL")


def get_version() -> str:
    default = "0.1.0"
    ver = Path(__file__).parent.parent / "version.txt"
    if ver.exists() and ver.is_file():
        with open(ver, encoding="utf-8") as f_o:
            line = f_o.readline().strip()
            return line if line else default
    return default


def singleton(
    class_: Callable[[VarArg(List[Any]), KwArg(Dict[str, Any])], Any]
) -> Callable[[VarArg(Any)], Any]:
    """Singleton pattern implementation"""
    instances = {}

    def getinstance(*args: List[Any], **kwargs: Dict[str, Any]) -> Any:
        """Sets the possibility of creating an instance of the class in the singular"""
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
def get_request_session(*args: List[Any], **kwargs: Dict[str, Any]) -> Session:
    """
    Establishes session and sets basic settings
    Return:
        session object
    """
    s = Session()
    retries = Retry(
        total=3, backoff_factor=1, status_forcelist=[500, 501, 502, 503, 504]
    )
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s


settings = Settings()
logger_.info(f"{settings.s3_credentials_provider=}")


class NotConfiguredException(Exception):
    pass


def create_boto3_config():
    boto3_config = {}
    if settings.s3_credentials_provider == "minio":
        boto3_config.update(
            {
                "aws_access_key_id": settings.minio_access_key,
                "aws_secret_access_key": settings.minio_secret_key,
                "endpoint_url": settings.minio_host,
            }
        )
    elif settings.s3_credentials_provider == "aws_iam":
        # No additional updates to config needed - boto3 uses env vars
        ...
    else:
        raise NotConfiguredException(
            "s3 connection is not properly configured - "
            "s3_credentials_provider is not set"
        )
    logger_.info(
        f"S3_Credentials provider - {settings.s3_credentials_provider}"
    )
    return boto3_config


def get_minio_client() -> BaseClient:
    """Initialized s3 client by boto3 client"""
    boto3_config = create_boto3_config()
    client = boto3.client("s3", **boto3_config)
    return client


def get_minio_resource() -> BaseClient:
    """Initialized s3 client by boto3 resource"""
    boto3_config = create_boto3_config()
    client = boto3.resource("s3", **boto3_config)
    return client


API_VERSION = get_version()
API_NAME = "convert"

minio_client = get_minio_client()
minio_resource = get_minio_resource()
