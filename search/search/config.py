import pathlib
from typing import List, Optional

from dotenv import find_dotenv
from pydantic import BaseSettings
from pydantic.fields import Field


def get_version() -> str:
    default = "0.1.0"
    ver = pathlib.Path(__file__).parent.parent / "version.txt"
    if ver.exists() and ver.is_file():
        with open(ver, "r", encoding="utf-8") as version_info:
            line = version_info.readline().strip()
            return line or default

    return default


class Settings(BaseSettings):
    app_title: str
    annotation_url: str
    annotation_categories: str
    annotation_categories_search: str
    es_host: str
    es_port: int
    es_host_test: str
    es_port_test: int
    s3_endpoint_url: str
    s3_login: str
    s3_pass: str
    s3_start_path: str
    s3_credentials_provider: Optional[str]
    s3_prefix: Optional[str]
    version: str = Field(default_factory=get_version)
    manifest: str
    text_pieces_path: str
    indexation_path: str
    root_path: str = ""
    keycloak_url: str
    jwt_algorithm: str
    kafka_bootstrap_server: str
    kafka_group_id: str
    kafka_search_topic: str
    kafka_search_topic_partitions: int
    kafka_search_replication_factor: int
    jobs_url: str
    jobs_search: str
    computed_fields: List[str]

    @property
    def annotation_categories_url(self) -> str:
        return "/".join(
            (
                self.annotation_url.rstrip("/"),
                self.annotation_categories.lstrip("/"),
            )
        )

    @property
    def annotation_categories_search_url(self) -> str:
        return "/".join(
            (
                self.annotation_url.rstrip("/"),
                self.annotation_categories_search.lstrip("/"),
            )
        )

    @property
    def jobs_search_url(self) -> str:
        return "/".join(
            (self.jobs_url.rstrip("/"), self.jobs_search.lstrip("/"))
        )

    class Config:
        env_file: str = find_dotenv(".env")
        env_file_encoding = "utf-8"


settings = Settings()
