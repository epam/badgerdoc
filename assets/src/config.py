from pathlib import Path
from typing import List, Optional

from dotenv import find_dotenv
from pydantic import BaseSettings, Field


def get_version() -> str:
    default = "0.1.0"
    ver = Path(__file__).parent.parent / "version.txt"
    if ver.exists() and ver.is_file():
        with open(ver, "r", encoding="utf-8") as file:
            line = file.readline().strip()
            return line or default

    return default


class Config(BaseSettings):
    uploading_limit: int = Field(100, env="UPLOADING_LIMIT")
    width: int = Field(450, env="WIDTH")
    bbox_ext: int = 100
    app_name: Optional[str] = "assets"
    app_version: Optional[str] = Field(default_factory=get_version)
    postgres_user: Optional[str]
    postgres_password: Optional[str]
    postgres_db: Optional[str]
    postgres_host: Optional[str]
    postgres_port: Optional[str]
    database_url: Optional[str]
    s3_credentials_provider: Optional[str]
    s3_endpoint: Optional[str]
    s3_access_key: Optional[str]
    s3_secret_key: Optional[str]
    s3_prefix: Optional[str]
    minio_secure_connection: Optional[bool] = False
    preprocessing_url: Optional[str]
    sqlalchemy_pool_size: Optional[int] = 10
    test_region: Optional[str]
    preprocessing_chunk_size: Optional[int]
    root_path: Optional[str] = ""
    log_file: Optional[bool] = False
    keycloak_uri: Optional[str]
    gotenberg: Optional[str]
    gotenberg_libre_office_endpoint: Optional[str]
    gotenberg_formats: List[str]
    image_formats: List[str]
    aws_profile_name: Optional[str]

    class Config:
        env_file: str = find_dotenv(".env")
        env_file_encoding = "utf-8"


settings = Config()
