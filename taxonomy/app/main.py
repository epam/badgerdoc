import os
import pathlib

from dotenv import find_dotenv, load_dotenv
from fastapi import Depends, FastAPI
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from app.errors import (
    CheckFieldError,
    FieldConstraintError,
    ForeignKeyError,
    NoTaxonError,
    NoTaxonomyError,
    SelfParentError,
    check_field_error_handler,
    db_dbapi_error_handler,
    db_sa_error_handler,
    field_constraint_error_handler,
    foreign_key_error_handler,
    no_taxon_error_handler,
    no_taxonomy_error_handler,
    taxon_parent_child_error_handler,
)
from app.tags import TAGS
from app.taxon import resources as taxon_resources
from app.taxonomy import resources as taxonomy_resources
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
    title="Badgerdoc Taxonomy",
    version=get_version(),
    openapi_tags=TAGS,
    root_path=ROOT_PATH,
    dependencies=[Depends(TOKEN)],
)

app.include_router(taxon_resources.router)
app.include_router(taxonomy_resources.router)

app.add_exception_handler(CheckFieldError, check_field_error_handler)
app.add_exception_handler(FieldConstraintError, field_constraint_error_handler)
app.add_exception_handler(ForeignKeyError, foreign_key_error_handler)
app.add_exception_handler(NoTaxonomyError, no_taxonomy_error_handler)
app.add_exception_handler(NoTaxonError, no_taxon_error_handler)
app.add_exception_handler(SelfParentError, taxon_parent_child_error_handler)
app.add_exception_handler(SQLAlchemyError, db_sa_error_handler)
app.add_exception_handler(DBAPIError, db_dbapi_error_handler)
