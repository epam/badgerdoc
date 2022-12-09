from typing import Union

from botocore.exceptions import BotoCoreError, ClientError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from requests import RequestException
from sqlalchemy.exc import DBAPIError, SQLAlchemyError


class NoSuchRevisionsError(Exception):
    pass


class CheckFieldError(Exception):
    def __init__(self, message: str):
        self.message = message


class EnumValidationError(Exception):
    def __init__(self, message: str):
        self.message = message


class FieldConstraintError(Exception):
    def __init__(self, message: str):
        self.message = message


class ForeignKeyError(Exception):
    def __init__(self, message: str):
        self.message = message


class NoSuchCategoryError(Exception):
    def __init__(self, message: str):
        self.message = message


class WrongJobError(Exception):
    def __init__(self, job_id):
        self.job_id = job_id


class SelfParentError(Exception):
    def __init__(self, message: str):
        self.message = message


class TaxonomyLinkException(Exception):
    def __init__(self, exc_info: Union[str, RequestException]):
        self.exc_info = exc_info


def no_such_revisions_error_handler(
    request: Request, exc: NoSuchRevisionsError
):
    return JSONResponse(
        status_code=404,
        content={"detail": "Cannot find such revision(s)."},
    )


def wrong_job_error_handler(request: Request, exc: WrongJobError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Error: Job with job_id ({exc.job_id}) not found"},
    )


def no_such_category_error_handler(request: Request, exc: NoSuchCategoryError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"{exc.message}. Check your request arguments."},
    )


def category_unique_field_error_handler(
    request: Request, exc: CheckFieldError
):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Field constraint error. {exc.message}"},
    )


def category_foreign_key_error_handler(request: Request, exc: ForeignKeyError):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Foreign key error. {exc.message}"},
    )


def db_sa_error_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: connection error ({exc})"},
    )


def db_dbapi_error_handler(request: Request, exc: DBAPIError):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: connection error ({exc})"},
    )


def db_s3_error_handler(request: Request, exc: BotoCoreError):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error: connection error ({exc})"},
    )


def minio_no_such_bucket_error_handler(request: Request, exc: ClientError):
    return JSONResponse(
        status_code=500,
        content={"detail": "Error: No such bucket."},
    )


def field_constraint_error_handler(
    request: Request, exc: FieldConstraintError
):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Error: {exc.message}"},
    )


def enum_validation_error_handler(request: Request, exc: EnumValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": f"Error: ({exc.message})."},
    )


def category_parent_child_error_handler(
    request: Request, exc: SelfParentError
):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Self parent error. {exc.message}"},
    )


def taxonomy_link_error_handler(request: Request, exc: TaxonomyLinkException):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Taxonomy link error. {exc.exc_info}"},
    )
