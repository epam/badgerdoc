import pathlib
from typing import List, Optional
import os

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

def get_service_uri(prefix: str) -> str:  # noqa
    service_scheme = os.getenv(f"{prefix}SERVICE_SCHEME")
    service_host = os.getenv(f"{prefix}SERVICE_HOST")
    service_port = os.getenv(f"{prefix}SERVICE_PORT")
    if service_port and service_host and service_scheme:
        return f"{service_scheme}://{service_host}:{service_port}"
    return ""


class Settings(BaseSettings):
    app_title: str
    annotation_service_uri: Optional[str] = get_service_uri("ANNOTATION_")
    jobs_service_uri: Optional[str] = get_service_uri("JOBS_")
    embed_host_uri: Optional[str] = get_service_uri("EMBED_")
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
    s3_text_path: str
    s3_credentials_provider: Optional[str]
    s3_prefix: Optional[str]
    version: str = Field(default_factory=get_version)
    manifest: str
    text_pieces_path: str
    indexation_path: str
    root_path: str = ""
    keycloak_host: str
    jwt_algorithm: str
    kafka_bootstrap_server: str
    kafka_group_id: str
    kafka_search_topic: str
    kafka_search_topic_partitions: int
    kafka_search_replication_factor: int
    jobs_search: str
    computed_fields: List[str]
    embed_sent_path: str
    embed_responses_path: str
    embed_question_path: str
    text_category: int
    chatgpt_api_key: str
    chatgpt_model: str

    @property
    def embed_responses_url(self) -> str:
        return f"{settings.embed_host_uri}{settings.embed_responses_path}"

    @property
    def embed_question_url(self) -> str:
        return f"{settings.embed_host_uri}{settings.embed_question_path}"


    @property
    def embed_url(self) -> str:
        return f"{self.embed_host_uri}{self.embed_sent_path}"

    @property
    def annotation_categories_url(self) -> str:
        return "/".join(
            (
                self.annotation_service_uri.rstrip("/"),
                self.annotation_categories.lstrip("/"),
            )
        )

    @property
    def annotation_categories_search_url(self) -> str:
        return "/".join(
            (
                self.annotation_service_uri.rstrip("/"),
                self.annotation_categories_search.lstrip("/"),
            )
        )

    @property
    def jobs_search_url(self) -> str:
        return f"{self.jobs_service_uri}/jobs/search"


    class Config:
        env_file: str = find_dotenv(".env")
        env_file_encoding = "utf-8"


settings = Settings()
''