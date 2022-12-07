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


VERSION = get_version()

# App settings.
HEARTBEAT_TIMEOUT = int(os.getenv("HEARTBEAT_TIMEOUT", 15))
THRESHOLD_MUL = int(os.getenv("HEARTBEAT_THRESHOLD_MUL", 10))
RUNNER_TIMEOUT = int(os.getenv("RUNNER_TIMEOUT", 5))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 15))
ANNOTATION_URI = os.getenv("ANNOTATION_URI", "")
POSTPROCESSING_URI = os.getenv("PROCESSING_URI", "")
MODELS_URI = os.getenv("MODELS_URI", "")
ASSETS_URI = os.getenv("ASSETS_URI", "")
MODELS_DEPLOYMENT_ENDPOINT = os.getenv("MODELS_DEPLOYMENT_ENDPOINT", "")
MODELS_SEARCH_ENDPOINT = os.getenv("MODELS_SEARCH_ENDPOINT", "")
DEBUG_MERGE = True if os.getenv("DEBUG_MERGE") == "True" else False
ROOT_PATH = os.getenv("ROOT_PATH", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# SQLAlchemy settings.
POOL_SIZE = int(os.getenv("SA_POOL_SIZE", 0))

# Database (PostgreSQL) settings.
DB_USERNAME = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pipelines")
DB_URI = os.getenv(
    "DB_URI",
    f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

# S3 settings
S3_CREDENTIALS_PROVIDER = os.getenv("S3_CREDENTIALS_PROVIDER")
S3_PREFIX = os.getenv("S3_PREFIX", "")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
AWS_PROFILE = os.getenv("AWS_PROFILE")

# Keycloak settings
KEYCLOAK_URI = os.getenv("KEYCLOAK_URI", "http://dev1.badgerdoc.com")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
KEYCLOAK_TOKEN_URI = (
    f"{KEYCLOAK_URI}/auth/realms/{KEYCLOAK_REALM}" f"/protocol/openid-connect/token"
)

# Kafka settings
KAFKA_BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
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
