from subprocess import SubprocessError

from botocore.exceptions import BotoCoreError, ClientError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from paramiko.ssh_exception import SSHException
from sqlalchemy.exc import SQLAlchemyError


class NoSuchTenant(Exception):
    def __init__(self, message: str):
        self.message = message


class ColabFileUploadError(Exception):
    def __init__(self, message: str):
        self.message = message


def botocore_error_handler(request: Request, exc: BotoCoreError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: connection error ({exc})"},
    )


def minio_client_error_handler(request: Request, exc: ClientError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: client error ({exc})"},
    )


def minio_no_such_bucket_error_handler(
    request: Request, exc: NoSuchTenant
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Error: No bucket for tenant. {exc}"},
    )


def ssh_connection_error_handler(request: Request, exc: SSHException) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: ssh connection error ({exc})"},
    )


def colab_execution_error_handler(
    request: Request, exc: ColabFileUploadError
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: Colab interaction error ({exc})"},
    )


def sqlalchemy_db_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: connection error ({exc})"},
    )


def subprocess_called_error_handler(
    request: Request, exc: SubprocessError
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: subprocess execution error ({exc})"},
    )
