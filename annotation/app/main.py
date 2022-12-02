import os
import pathlib

from botocore.exceptions import BotoCoreError, ClientError
from dotenv import find_dotenv, load_dotenv
from fastapi import Depends, FastAPI
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from app.annotations import resources as annotations_resources
from app.categories import resources as categories_resources
from app.distribution import resources as distribution_resources
from app.errors import (
    CheckFieldError,
    EnumValidationError,
    FieldConstraintError,
    ForeignKeyError,
    NoSuchCategoryError,
    NoSuchRevisionsError,
    SelfParentError,
    TaxonomyLinkException,
    WrongJobError,
    category_foreign_key_error_handler,
    category_parent_child_error_handler,
    category_unique_field_error_handler,
    db_dbapi_error_handler,
    db_s3_error_handler,
    db_sa_error_handler,
    enum_validation_error_handler,
    field_constraint_error_handler,
    minio_no_such_bucket_error_handler,
    no_such_category_error_handler,
    no_such_revisions_error_handler,
    taxonomy_link_error_handler,
    wrong_job_error_handler,
)
from app.jobs import resources as jobs_resources
from app.metadata import resources as metadata_resources
from app.revisions import resources as revision_resources
from app.tags import TAGS
from app.tasks import resources as task_resources
from app.token_dependency import TOKEN

load_dotenv(find_dotenv())

ROOT_PATH = os.environ.get("ROOT_PATH", "")


def get_version() -> str:
    default = "0.1.0"
    ver = pathlib.Path(__file__).parent.parent / "version.txt"
    if ver.exists() and ver.is_file():
        with open(ver, "r", encoding="utf-8") as version_info:
            line = version_info.readline().strip()
            return line or default

    return default


app = FastAPI(
    title="Badgerdoc Annotation",
    version=get_version(),
    openapi_tags=TAGS,
    root_path=ROOT_PATH,
    dependencies=[Depends(TOKEN)],
)

app.include_router(annotations_resources.router)
app.include_router(task_resources.router)
app.include_router(distribution_resources.router)
app.include_router(metadata_resources.router)
app.include_router(jobs_resources.router)
app.include_router(categories_resources.router)
app.include_router(revision_resources.router)

app.add_exception_handler(
    NoSuchRevisionsError, no_such_revisions_error_handler
)
app.add_exception_handler(CheckFieldError, category_unique_field_error_handler)
app.add_exception_handler(EnumValidationError, enum_validation_error_handler)
app.add_exception_handler(FieldConstraintError, field_constraint_error_handler)
app.add_exception_handler(ForeignKeyError, category_foreign_key_error_handler)
app.add_exception_handler(NoSuchCategoryError, no_such_category_error_handler)
app.add_exception_handler(WrongJobError, wrong_job_error_handler)
app.add_exception_handler(BotoCoreError, db_s3_error_handler)
app.add_exception_handler(ClientError, minio_no_such_bucket_error_handler)
app.add_exception_handler(SQLAlchemyError, db_sa_error_handler)
app.add_exception_handler(DBAPIError, db_dbapi_error_handler)
app.add_exception_handler(SelfParentError, category_parent_child_error_handler)
app.add_exception_handler(TaxonomyLinkException, taxonomy_link_error_handler)
