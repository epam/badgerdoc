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
    log_level: int = logging.INFO
    minio_log_file_bucket = "post"
    minio_log_file_path = "log.log"

    local_run: bool = False

    app_name: str = "processing"
    app_version: str = Field(default_factory=get_version)
    root_path: str = "/api/v1/processing"

    minio_server: str = "minio:80"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"
    minio_secure_connection: Optional[bool] = False
    s3_prefix: Optional[str]
    s3_credentials_provider: Optional[str]
    aws_profile_name: Optional[str]

    keycloak_host: str = "http://bagerdoc-keycloack"
    host_models: str = "http://models/deployed_models"
    host_pipelines: str = "http://pipelines"
    host_assets: str = "http://assets"
    external_postfix: str = ".badgerdoc.com"
    preprocessing_url: Optional[str]

    max_tasks: int = 10  # max amount of tasks that this service can processing simultaneously
    pages_per_batch = 3

    retry_attempts: int = 3
    retry_statuses: Set[int] = {501, 502, 503} | {i for i in range(505, 600)}
    delay_between_retry_attempts: int = 1  # in seconds
    request_timeout: int = 3 * 60 * 60

    db_username: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str
    service_name: str

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
            f"{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def assets_url(self) -> str:
        return "/".join((self.host_assets.rstrip("/"), "files"))

    def get_webhook(self, endpoint: str) -> str:
        return "/".join(
            (f"http://{self.service_name}".rstrip("/"), endpoint.lstrip("/"))
        )


settings = Settings()
