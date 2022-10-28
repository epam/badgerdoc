from typing import Any, Dict, Tuple, Type

from sqlalchemy import func
from sqlalchemy.exc import ArgumentError, DataError, ProgrammingError
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.query import Query
from sqlalchemy_filters import apply_filters, apply_sort
from sqlalchemy_filters.exceptions import BadFilterFormat, BadSpec

from .pagination import PaginationParams, make_pagination
from .schema_generator import Pagination


def form_query(
    args: Dict[str, Any], query: Query
) -> Tuple[Query, PaginationParams]:
    filters = args.get("filters")
    sorting = args.get("sorting")
    pagination = args.get("pagination")

    if filters:
        for fil in filters:
            query = _create_filter(query, fil)

    if sorting:
        for sor in sorting:
            query = apply_sort(query, sor)

    if not pagination:
        pagination = Pagination(page_num=1, page_size=15).dict()
    try:
        query, pag = make_pagination(
            query, pagination["page_num"], pagination["page_size"]
        )
    except (ProgrammingError, DataError) as e:
        raise BadFilterFormat(f"{e.params}")
    return query, pag


def _get_entity(query: Query, model_name: str) -> Type[DeclarativeMeta]:
    properties = query.column_descriptions
    for element in properties:
        if element["name"] == model_name:
            return element["entity"]  # type: ignore
    else:
        raise BadSpec(f"Provided query has no model {model_name}")


def _get_column(
    model: Type[DeclarativeMeta], column_name: str
) -> InstrumentedAttribute:
    try:
        return getattr(model, column_name)
    except AttributeError as e:
        raise BadSpec(f"{e}")


def _create_filter(query: Query, fil: Dict[str, Any]) -> Query:
    if fil.get("op") == "match" and fil.get("model"):
        model = _get_entity(query, fil["model"])
        column = _get_column(model, fil["field"])
        query = _make_match(query, column, fil["value"])
    else:
        try:
            query = apply_filters(query, fil, do_auto_join=False)
        except ArgumentError as e:
            raise BadFilterFormat(f"{e.args}")
    return query


def _make_match(
    query: Query,
    field: InstrumentedAttribute,
    value: str,
    language: str = "english",
) -> Query:
    query = query.filter(field.op("@@")(func.plainto_tsquery(language, value)))
    return query
