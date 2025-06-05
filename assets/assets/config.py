from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_version() -> str:
    default = "0.1.0"
    ver = Path(__file__).parent.parent / "version.txt"
    if ver.exists() and ver.is_file():
        with open(ver, "r", encoding="utf-8") as file:
            line = file.readline().strip()
            return line or default

    return default


class Config(BaseSettings):
    uploading_limit: int = Field(100, validation_alias="UPLOADING_LIMIT")
    width: int = Field(450, validation_alias="WIDTH")
    bbox_ext: int = 100
    app_name: Optional[str] = "assets"
    app_version: Optional[str] = Field(default_factory=get_version)
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_host: Optional[str] = None
    postgres_port: Optional[str] = None
    database_url: Optional[str] = None
    storage_provider: Optional[str] = None
    s3_endpoint: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_prefix: Optional[str] = None
    s3_secure: Optional[bool] = False
    preprocessing_url: Optional[str] = None
    sqlalchemy_pool_size: Optional[int] = 10
    aws_region: Optional[str] = None
    preprocessing_chunk_size: Optional[int] = None
    root_path: Optional[str] = ""
    log_file: Optional[bool] = False
    keycloak_host: Optional[str] = None
    gotenberg_host: Optional[str] = None
    gotenberg_libre_office_endpoint: Optional[str] = None
    gotenberg_chromium_endpoint: Optional[str] = None
    gotenberg_formats: List[str]
    image_formats: List[str]
    aws_profile_name: Optional[str] = None
    convert_service_scheme: Optional[str] = None
    convert_service_host: Optional[str] = None
    convert_service_port: Optional[int] = None
    convert_service_pdf_endpoint: Optional[str] = None
    convert_service_txt_endpoint: Optional[str] = None
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8", env_file=".env", extra="ignore"
    )

    @property
    def service_convert_pdf(self):
        if self.convert_service_host and self.convert_service_scheme:
            port_str = (
                f":{self.convert_service_port}"
                if self.convert_service_port is not None
                else ""
            )  # noqa
            return f"{self.convert_service_scheme}://{self.convert_service_host}{port_str}{self.convert_service_pdf_endpoint}"  # noqa

        return None

    @property
    def service_convert_txt(self):
        if self.convert_service_host and self.convert_service_scheme:
            port_str = (
                f":{self.convert_service_port}"
                if self.convert_service_port is not None
                else ""
            )  # noqa
            return f"{self.convert_service_scheme}://{self.convert_service_host}{port_str}{self.convert_service_txt_endpoint}"  # noqa

        return None


settings = Config()
