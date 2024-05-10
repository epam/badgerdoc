import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_version() -> str:
    """Get app version from version.txt in the root directory."""
    default = "0.1.0"
    ver_file = "version.txt"
    file = Path(__file__).parent.parent / ver_file
    if not (file.exists() and file.is_file()):
        return default
    with open(file, "r", encoding="utf-8") as f_o:
        return f_o.readline().strip() or default


def get_service_uri(prefix: str) -> str:  # noqa
    service_scheme = os.getenv(f"{prefix}SERVICE_SCHEME")
    service_host = os.getenv(f"{prefix}SERVICE_HOST")
    service_port = os.getenv(f"{prefix}SERVICE_PORT")
    if service_port and service_host and service_scheme:
        return f"{service_scheme}://{service_host}:{service_port}"
    return ""


VERSION = get_version()

# App settings.
HEARTBEAT_TIMEOUT = int(os.getenv("HEARTBEAT_TIMEOUT", 15))
THRESHOLD_MUL = int(os.getenv("HEARTBEAT_THRESHOLD_MUL", 10))
RUNNER_TIMEOUT = int(os.getenv("RUNNER_TIMEOUT", 5))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 15))

ANNOTATION_URI = get_service_uri("ANNOTATION_")
PROCESSING_URI = get_service_uri("PROCESSING_")
MODELS_URI = get_service_uri("MODELS_")
ASSETS_URI = get_service_uri("ASSETS_")

MODELS_DEPLOYMENT_ENDPOINT = os.getenv("MODELS_DEPLOYMENT_ENDPOINT", "")
MODELS_SEARCH_ENDPOINT = os.getenv("MODELS_SEARCH_ENDPOINT", "")
DEBUG_MERGE = True if os.getenv("DEBUG_MERGE") == "True" else False
ROOT_PATH = os.getenv("ROOT_PATH", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# SQLAlchemy settings.
POOL_SIZE = int(os.getenv("SA_POOL_SIZE", 0))

# Database (PostgreSQL) settings.
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "pipelines")
DB_URI = os.getenv(
    "DB_URI",
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)

# S3 settings
S3_PROVIDER = os.getenv("S3_PROVIDER")
S3_PREFIX = os.getenv("S3_PREFIX", "")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
AWS_PROFILE = os.getenv("AWS_PROFILE")
MINIO_SECURE_CONNECTION = os.getenv(
    "MINIO_SECURE_CONNECTION", "False"
).lower() in ("true", "1")

# Keycloak settings
KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST", "http://dev1.badgerdoc.com")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_TOKEN_URI = (
    f"{KEYCLOAK_HOST}/auth/realms/{KEYCLOAK_REALM}"
    f"/protocol/openid-connect/token"
)

# Kafka settings
KAFKA_BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER", "kafka:9092")
KAFKA_CONSUME_TOPIC = os.getenv("KAFKA_CONSUME_TOPIC", "scheduler")
KAFKA_PRODUCE_TOPIC = os.getenv("KAFKA_PRODUCE_TOPIC", "pipelines")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "pipelines_group")
KAFKA_TOPICS_PARTITIONS = os.getenv("KAFKA_TOPICS_PARTITIONS", 1)
KAFKA_REPLICATION_FACTORS = os.getenv("KAFKA_REPLICATION_FACTORS", 1)

# Temporary alternative urls for preprocessing models
DIFFERENT_PREPROCESSING_URLS = True

# Preprocessing settings
MAX_FILE_STATUS_RETRIES = os.getenv("MAX_FILE_STATUS_RETRIES", 100000)
FILE_STATUS_TIMEOUT = os.getenv("FILE_STATUS_TIMEOUT", 10)

# Airflow settings
AIRFLOW_URL = get_service_uri("AIRFLOW_") + os.getenv(
    "AIRFLOW_SERVICE_PATH_PREFIX", "/api/v1"
)
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD")
