import os
from typing import Collection

from fastapi import HTTPException


def get_test_db_url(main_db_url: str) -> str:
    """
    Takes main database url and returns test database url.

    Example:
    postgresql+psycopg2://admin:admin@host:5432/service_name ->
    postgresql+psycopg2://admin:admin@host:5432/test_db
    """
    main_db_url_split = main_db_url.split("/")
    main_db_url_split[-1] = "test_db"
    result = "/".join(main_db_url_split)
    return result


def get_service_uri(prefix: str) -> str:  # noqa
    service_scheme = os.getenv(f"{prefix}SERVICE_SCHEME")
    service_host = os.getenv(f"{prefix}SERVICE_HOST")
    service_port = os.getenv(f"{prefix}SERVICE_PORT")
    if service_port and service_host and service_scheme:
        return f"{service_scheme}://{service_host}:{service_port}"
    return ""


def validate_ge(
    collection: Collection, ge_value: int = 1, field_name: str = "collection"
):
    """
    Ensures all items in a collection are >= ge_value.

    :param collection: List, Set, etc.
    :param ge_value: Minimum allowed value.
    :param field_name: Name of the field for error messages.
    :raises HTTPException: If any item is below ge_value.
    """
    invalid_items = [item for item in collection if item < ge_value]
    if invalid_items:
        raise HTTPException(
            status_code=422,
            detail=(
                f"All elements in '{field_name}' must be >= {ge_value}. "
                f"Invalid: {invalid_items}."
            ),
        )
