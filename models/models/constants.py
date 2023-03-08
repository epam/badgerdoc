import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv("./src/.env"))

POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB = os.environ.get("POSTGRES_DB")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", 5432)
DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY")
MINIO_HOST = os.environ.get("MINIO_HOST")
MINIO_PUBLIC_HOST = os.environ.get("MINIO_PUBLIC_HOST")
S3_PREFIX = os.environ.get("S3_PREFIX")
S3_CREDENTIALS_PROVIDER = os.environ.get("S3_CREDENTIALS_PROVIDER")

INFERENCE_HOST = os.environ.get("INFERENCE_HOST")
INFERENCE_PORT = os.environ.get("INFERENCE_PORT")

ALGORITHM = os.environ.get("ALGORITHM", "RS256")
SECRET = os.environ.get("SECRET")
KEYCLOACK_URI = os.environ.get("KEYCLOACK_URI", "http://bagerdoc-keycloack")

DOCKER_REGISTRY_URL = os.environ.get("DOCKER_REGISTRY_URL")
DOMAIN_NAME = os.environ.get("DOMAIN_NAME")
MODELS_NAMESPACE = os.environ.get("MODELS_NAMESPACE")
ROOT_PATH = os.environ.get("ROOT_PATH")

CONVERT_EXPORT_URL = os.environ.get("CONVERT_EXPORT_URL")
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
