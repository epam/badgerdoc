import logging
import sys
from pathlib import Path
from subprocess import SubprocessError

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI
from paramiko.ssh_exception import SSHException
from sqlalchemy.exc import SQLAlchemyError

from models.constants import API_NAME, API_VERSION, ROOT_PATH
from models.errors import (
    ColabFileUploadError,
    NoSuchTenant,
    botocore_error_handler,
    colab_execution_error_handler,
    minio_client_error_handler,
    minio_no_such_bucket_error_handler,
    sqlalchemy_db_error_handler,
    ssh_connection_error_handler,
    subprocess_called_error_handler,
)
from models.routers import (
    basements_routers,
    deployed_models_routers,
    models_routers,
    training_routers,
)

LOGGER = logging.getLogger(name=API_NAME)
LOGGING_FORMAT = "[%(asctime)s] - [%(name)s] - [%(levelname)s] - [%(message)s]"


def configure_logging() -> None:
    formatter = logging.Formatter(LOGGING_FORMAT)
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)
    ROOT = Path(__file__).parent
    LOG_FILE = str(ROOT.joinpath(f"{API_NAME}.log"))
    Path(LOG_FILE).touch()
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(console_handler)
    logging.root.addHandler(file_handler)


configure_logging()

app = FastAPI(
    title=API_NAME,
    description=(
        "This service implements CRUD operations for models, "
        "basements (docker images) and trainings. Also it has endpoints "
        "to deploy/undeploy models on Knative."
    ),
    version=API_VERSION,
    root_path=ROOT_PATH,
    servers=[{"url": ROOT_PATH}],
)
app.include_router(basements_routers.router)
app.include_router(models_routers.router)
app.include_router(training_routers.router)
app.include_router(deployed_models_routers.router)

app.add_exception_handler(BotoCoreError, botocore_error_handler)
app.add_exception_handler(ColabFileUploadError, colab_execution_error_handler)
app.add_exception_handler(ClientError, minio_client_error_handler)
app.add_exception_handler(NoSuchTenant, minio_no_such_bucket_error_handler)
app.add_exception_handler(SSHException, ssh_connection_error_handler)
app.add_exception_handler(SSHException, ssh_connection_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_db_error_handler)
app.add_exception_handler(SubprocessError, subprocess_called_error_handler)
