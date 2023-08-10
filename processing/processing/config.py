import logging
from pathlib import Path
from typing import Optional, Set

from dotenv import find_dotenv
from pydantic import BaseSettings, Field, validator


def get_version() -> str:
    default = "0.1.0"
    ver = Path(__file__).parent.parent / "version.txt"
    if ver.exists() and ver.is_file():
        with open(ver, "r", encoding="utf-8") as file:
            line = file.readline().strip()
            return line or default

    return default


# pylint: disable=E0213
class Settings(BaseSettings):
    log_file: Path = Path("./log.log")
    log_level: str = "INFO"
    minio_log_file_bucket = "post"
    minio_log_file_path = "log.log"

    app_name: str = "processing"
    app_version: str = Field(default_factory=get_version)

    s3_prefix: Optional[str]
    s3_provider: Optional[str]
    aws_profile_name: Optional[str]

    external_postfix: str = ".badgerdoc.com"
    preprocessing_url: Optional[str]

    max_tasks: int = 10  # max amount of tasks that this
    # service can processing simultaneously
    pages_per_batch = 3

    retry_attempts: int = 3
    retry_statuses: Set[int] = {501, 502, 503} | {i for i in range(505, 600)}
    delay_between_retry_attempts: int = 1  # in seconds
    request_timeout: int = 3 * 60 * 60

    root_path: str

    assets_service_host: str
    models_service_host: str
    keycloak_host: str
    pipelines_service_host: str

    s3_endpoint: str
    s3_secret_key: str
    s3_access_key: str
    s3_secure: bool

    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    postgres_db: str

    processing_service_host: str

    class Config:
        env_file: str = find_dotenv(".env")
        env_file_encoding = "utf-8"

    @validator("log_file")
    def create_log_file(cls, log_file: Path) -> Path:
        log_file.parent.mkdir(exist_ok=True, parents=True)
        return log_file

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def assets_url(self) -> str:
        return "/".join((self.assets_service_host.rstrip("/"), "files"))

    def get_webhook(self, endpoint: str) -> str:
        return "/".join(
            (f"http://{self.processing_service_host}".rstrip("/"), endpoint.lstrip("/"))
        )


settings = Settings()
