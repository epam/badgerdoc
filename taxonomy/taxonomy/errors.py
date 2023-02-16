from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, SQLAlchemyError


class CheckFieldError(Exception):
    def __init__(self, message: str):
        self.message = message


class FieldConstraintError(Exception):
    def __init__(self, message: str):
        self.message = message


class ForeignKeyError(Exception):
    def __init__(self, message: str):
        self.message = message


class NoTaxonomyError(Exception):
    def __init__(self, message: str):
        self.message = message


class NoTaxonError(Exception):
    def __init__(self, message: str):
        self.message = message


class SelfParentError(Exception):
    def __init__(self, message: str):
        self.message = message


def no_taxonomy_error_handler(request: Request, exc: NoTaxonomyError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"{exc.message}. Check your request arguments."},
    )


def no_taxon_error_handler(request: Request, exc: NoTaxonError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"{exc.message}. Check your request arguments."},
    )


def check_field_error_handler(
    request: Request, exc: CheckFieldError
):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Field constraint error. {exc.message}"},
    )


def field_constraint_error_handler(
    request: Request, exc: FieldConstraintError
):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Error: {exc.message}"},
    )


def taxon_parent_child_error_handler(
    request: Request, exc: SelfParentError
):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Self parent error. {exc.message}"},
    )


def foreign_key_error_handler(request: Request, exc: ForeignKeyError):
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
