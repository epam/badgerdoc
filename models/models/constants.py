import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv("./src/.env"))

def get_service_uri(prefix: str) -> str:
    service_scheme=os.getenv(f"{prefix}SERVICE_SCHEME")
    service_host=os.getenv(f"{prefix}SERVICE_HOST")
    service_port=os.getenv(f"{prefix}SERVICE_PORT")

    if service_port and service_host and service_scheme:
        return f"{service_scheme}://{service_host}:{service_port}"
    return ""

POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB = os.environ.get("POSTGRES_DB")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", 5432)
DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

S3_SECURE = os.getenv(
    "S3_SECURE", "False"
).lower() in (
    "true",
    "1",
)
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT")
S3_PREFIX = os.environ.get("S3_PREFIX")
S3_CREDENTIALS_PROVIDER = os.environ.get("S3_CREDENTIALS_PROVIDER")

INFERENCE_HOST = os.environ.get("INFERENCE_HOST")
INFERENCE_PORT = os.environ.get("INFERENCE_PORT")

ALGORITHM = os.environ.get("ALGORITHM", "RS256")
KEYCLOAK_SYSTEM_USER_SECRET = os.environ.get("KEYCLOAK_SYSTEM_USER_SECRET")
KEYCLOAK_HOST = os.environ.get("KEYCLOAK_HOST", "http://bagerdoc-keycloack")

DOCKER_REGISTRY_URL = os.environ.get("DOCKER_REGISTRY_URL")
DOMAIN_NAME = os.environ.get("DOMAIN_NAME")
MODELS_NAMESPACE = os.environ.get("MODELS_NAMESPACE")
ROOT_PATH = os.environ.get("ROOT_PATH")

CONVERT_EXPORT_URL = get_service_uri("CONVERT_")
HEADER_TENANT = "X-Current-Tenant"

def get_version() -> str:
    default = "0.1.0"
    ver = Path(__file__).parent.parent / "version.txt"
    if ver.exists() and ver.is_file():
        with open(ver, "r", encoding="utf-8") as file:
            line = file.readline().strip()
            return line if line else default
    return default


API_VERSION = get_version()
API_NAME = "models"
CONTAINER_NAME = "inferenceservice"
