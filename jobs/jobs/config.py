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
POSTGRESQL_JOBMANAGER_DATABASE_URI = os.environ.get(
    "POSTGRESQL_JOBMANAGER_DATABASE_URI"
)

PIPELINES_URI = os.environ.get("PIPELINES_URI")
ASSETS_URI = os.environ.get("ASSETS_URI")
ANNOTATION_MICROSERVICE_URI = os.environ.get("ANNOTATION_MICROSERVICE_URI")
KEYCLOAK_HOST = os.environ.get("KEYCLOAK_HOST", "http://dev1.badgerdoc.com")
USERS_HOST = os.environ.get("USERS_HOST")

HOST_PIPELINES = "http://pipelines"
HOST_ASSETS = "http://assets"
HOST_ANNOTATION = "http://annotation"
HOST_TAXONOMY = "http://taxonomy"
JOBS_HOST = "http://jobs"

PAGINATION_THRESHOLD = 7
PROVIDE_JWT_IF_NO_ANY = True
