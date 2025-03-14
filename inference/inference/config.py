import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_version() -> str:
    default = "0.1.0"
    ver = Path(__file__).parent.parent / "version.txt"
    if ver.exists() and ver.is_file():
        with open(ver, "r", encoding="utf-8") as file:
            line = file.readline().strip()
            return line if line else default

    return default


def get_service_uri(prefix: str) -> str:  # noqa
    service_scheme = os.getenv(f"{prefix}SERVICE_SCHEME")
    service_host = os.getenv(f"{prefix}SERVICE_HOST")
    service_port = os.getenv(f"{prefix}SERVICE_PORT")
    if service_port and service_host and service_scheme:
        return f"{service_scheme}://{service_host}:{service_port}"
    return ""


API_current_version = get_version()

ROOT_PATH = os.environ.get("ROOT_PATH", default="/")

KEYCLOAK_HOST = os.environ.get("KEYCLOAK_HOST", "")
USERS_HOST = get_service_uri("USERS_")

PIPELINES_SERVICE_HOST = get_service_uri("PIPELINES_")
ASSETS_SERVICE_HOST = get_service_uri("ASSETS_")
ANNOTATION_SERVICE_HOST = get_service_uri("ANNOTATION_")
JOBS_SERVICE_HOST = get_service_uri("JOBS_")

# Airflow config
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD")
AIRFLOW_SERVICE_PORT = os.getenv("AIRFLOW_SERVICE_PORT")
AIRFLOW_SERVICE_SCHEME = os.getenv("AIRFLOW_SERVICE_SCHEME")
AIRFLOW_SERVICE_HOST = os.getenv("AIRFLOW_SERVICE_HOST")
AIRFLOW_SERVICE_PATH_PREFIX = os.getenv("AIRFLOW_SERVICE_PATH_PREFIX")

BADGERDOC_EXTERNAL_PORT = os.getenv("BADGERDOC_EXTERNAL_PORT")
