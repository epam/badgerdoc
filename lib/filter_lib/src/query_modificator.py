from typing import Any, Dict, List, Tuple, Type

from sqlalchemy import func
from sqlalchemy.exc import ArgumentError, DataError, ProgrammingError
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.query import Query
from sqlalchemy_filters import apply_filters, apply_sort
from sqlalchemy_filters.exceptions import BadFilterFormat, BadSpec
from sqlalchemy_utils import LtreeType

from .pagination import PaginationParams, make_pagination
from .schema_generator import Pagination


def splint_to_distinct_and_not(
    filters: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    distinct_filters, non_distinct_filters = [], []
    for fil in filters:
        distinct_filters.append(fil) if _op_is_distinct(
            fil
        ) else non_distinct_filters.append(fil)

    return distinct_filters, non_distinct_filters


def get_distinct_columns(
    query: Query, distinct_filters: List[Dict[str, Any]]
) -> List[InstrumentedAttribute]:
    result = []
    for fil in distinct_filters:
        model_name = fil.get("model")
        model_class = _get_entity(query, model_name)
        column_name = fil.get("field").value
        column_instance = _get_column(model_class, column_name)
        result.append(column_instance)
    return result


def form_query(
    args: Dict[str, Any], query: Query
) -> Tuple[Query, PaginationParams]:
    filters = args.get("filters")
    sorting = args.get("sorting")
    pagination = args.get("pagination")

    if filters:
        """All filters passed in are being divided into two groups -
        filters with 'distinct' operator and others.
        It's being done because DISTINCT statements should only be applied
        to query all at once, rather than one by one"""
        distinct_filters, non_distinct_filters = splint_to_distinct_and_not(
            filters
        )
        if distinct_filters:
            distinct_columns = get_distinct_columns(query, distinct_filters)
            query = query.with_entities(*distinct_columns).distinct(
                *distinct_columns
            )

        for fil in non_distinct_filters:
            query = _create_filter(query, fil)

    if sorting and not query._order_by:
        for sor in sorting:
            query = _create_sorting(query, sor)

    if not pagination:
        pagination = Pagination(page_num=1, page_size=15).dict()
    try:
        query, pag = make_pagination(
            query, pagination["page_num"], pagination["page_size"]
        )
    except (ProgrammingError, DataError) as e:
        raise BadFilterFormat(f"description: {e.orig}") from e

    return query, pag


def _get_entity(query: Query, model_name: str) -> Type[DeclarativeMeta]:
    properties = query.column_descriptions

    if query._distinct:
        entity = properties[0]["entity"]
        return entity  # type: ignore

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


def _create_sorting(query: Query, sor: Dict[str, Any]) -> Query:
    model = _get_entity(query, sor.get("model"))
    field = sor.get("field")

    if _has_relation(model, field):
        relation = getattr(model, field.split(".")[0])
        joined_tables = [mapper.class_ for mapper in query._join_entities]
        if relation.property.mapper.class_ not in joined_tables:
            query = query.join(relation)
        sor["field"] = field.split(".")[1]
        sor["model"] = relation.property.mapper.class_.__name__

    query = apply_sort(query, sor)
    return query


def _create_filter(query: Query, fil: Dict[str, Any]) -> Query:
    model = _get_entity(query, fil.get("model"))
    field = fil.get("field")
    op = fil.get("op")
    value = fil.get("value")

    if _has_relation(model, field) and _op_is_match(fil):
        raise BadFilterFormat(
            "Operator 'match' shouldn't be used with relations"
        )

    try:
        attr = getattr(model, field).type
    except AttributeError:
        attr = None

    if isinstance(attr, LtreeType):
        return _make_ltree_query(query=query, model=model, op=op, value=value)

    if _op_is_match(fil):
        column = _get_column(model, field)
        query = _make_match(query, column, value)
        return query

    if _has_relation(model, field):
        relation = getattr(model, field.split(".")[0])
        query = query.join(relation)
        fil["field"] = field.split(".")[1]
        fil["model"] = relation.property.mapper.class_.__name__

    if _op_is_not(fil):
        fil = _create_or_condition(fil)

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


def _has_relation(model: Type[DeclarativeMeta], field: str) -> bool:
    if (
        not hasattr(model, field)
        and hasattr(model, field.split(".")[0])
        and len(field.split(".")) == 2
    ):
        return True
    return False


def _op_is_match(fil: Dict[str, str]) -> bool:
    return fil.get("op") == "match"


def _op_is_distinct(fil: Dict[str, str]) -> bool:
    return fil.get("op") == "distinct"


def _op_is_not(fil: Dict[str, str]) -> bool:
    """Checks for `not` operators ( NOT EQUAL, NOT IN, NOT ILIKE)"""
    op = fil.get("op")
    return op == "ne" or op == "not_in" or op == "not_ilike"


def _make_ltree_query(
    query: Query, model: Type[DeclarativeMeta], op: str, value: int
) -> Query:
    """
    Makes query for LTREE field.
    Passes through income query if operation is not supported.

    Supported operations:
    - "parent" - return parent of record with provided id
    - "parents_recursive" - return all ancestors of record with provided id
    - "children" - get first-level children for record with provided id
    - "children_recursive" - get all descendants for record with provided id

    :param query: Initial model's query
    :param model: Model class
    :param op: Operation name
    :param value: Id of record
    :return: Query instance
    """
    subquery = (
        query.with_entities(model.tree).filter(model.id == value).subquery()
    )

    if op == "parent":
        return (
            query.filter(
                (
                    func.subpath(
                        model.tree, 0, func.nlevel(subquery.c.tree) - 1
                    )
                    == model.tree
                ),
                func.index(subquery.c.tree, model.tree) != -1,
            )
            .order_by(model.tree.desc())
            .limit(1)
        )
    elif op == "parents_recursive":
        return query.filter(
            func.nlevel(subquery.c.tree) != func.nlevel(model.tree),
            func.index(subquery.c.tree, model.tree) != -1,
        ).order_by(model.tree)
    elif op == "children":
        return query.filter(
            model.tree.op("<@")(subquery.c.tree),
            func.nlevel(model.tree) == func.nlevel(subquery.c.tree) + 1,
        )
    elif op == "children_recursive":
        return query.filter(
            model.tree.op("<@")(subquery.c.tree),
            func.nlevel(model.tree) > func.nlevel(subquery.c.tree),
        )

    return query


def _create_or_condition(
    fil: Dict[str, str]
) -> Dict[str, List[Dict[str, str]]]:
    fil_include_null = fil.copy()
    fil_include_null["op"] = "is_null"
    filter_args = {"or": [{**fil}, {**fil_include_null}]}
    return filter_args
