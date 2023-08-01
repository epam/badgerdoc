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

ASSETS_SERVICE_HOST = os.environ.get("ASSETS_SERVICE_HOST")
KEYCLOAK_HOST = os.environ.get("KEYCLOAK_HOST", "")
USERS_HOST = os.environ.get("USERS_HOST")

PIPELINES_SERVICE_HOST = f"http://{os.getenv('PIPELINES_SERVICE_HOST')}"
ASSETS_SERVICE_HOST = f"http://{os.getenv('ASSETS_SERVICE_HOST')}"
ANNOTATION_SERVICE_HOST = f"http://{os.getenv('ANNOTATION_SERVICE_HOST')}"
TAXONOMY_SERVICE_HOST = f"http://{os.getenv('TAXONOMY_SERVICE_HOST')}"
JOBS_SERVICE_HOST = f"http://{os.getenv('JOBS_SERVICE_HOST')}"

PAGINATION_THRESHOLD = 7
PROVIDE_JWT_IF_NO_ANY = True
