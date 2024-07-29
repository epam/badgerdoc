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

ROOT_PATH = os.environ.get("ROOT_PATH", default="")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

POSTGRESQL_JOBMANAGER_DATABASE_URI = (
    "postgresql+psycopg2://"
    f"{POSTGRES_USER}:{POSTGRES_USER}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}"
    f"/{POSTGRES_DB}"
)

KEYCLOAK_HOST = os.environ.get("KEYCLOAK_HOST", "")
USERS_HOST = get_service_uri("USERS_")

PIPELINES_SERVICE_HOST = get_service_uri("PIPELINES_")
ASSETS_SERVICE_HOST = get_service_uri("ASSETS_")
ANNOTATION_SERVICE_HOST = get_service_uri("ANNOTATION_")
TAXONOMY_SERVICE_HOST = get_service_uri("TAXONOMY_")
JOBS_SERVICE_HOST = get_service_uri("JOBS_")

PAGINATION_THRESHOLD = 7
PROVIDE_JWT_IF_NO_ANY = True

# S3 settings
STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER")
JOBS_SIGNED_URL_ENABLED = (
    os.getenv("JOBS_SIGNED_URL_ENABLED", "False").lower() == "true"
)
AWS_REGION = os.getenv("AWS_REGION")
S3_PREFIX = os.getenv("S3_PREFIX", "")
S3_SECURE = os.getenv("S3_SECURE", "False").lower() == "true"
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
AWS_PROFILE = os.getenv("AWS_PROFILE")
JOBS_SIGNED_URL_TTL = os.getenv("JOBS_SIGNED_URL_TTL", "")
JOBS_SIGNED_URL_TTL = (
    int(JOBS_SIGNED_URL_TTL) if JOBS_SIGNED_URL_TTL.isdigit() else 60
)
JOBS_SIGNED_URL_KEY_NAME = (
    os.getenv("JOBS_SIGNED_URL_KEY_NAME") or "signed_url"
)
