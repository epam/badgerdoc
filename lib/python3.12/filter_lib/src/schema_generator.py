import enum
from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.ext.declarative import DeclarativeMeta

from .enum_generator import get_enum_from_orm

TypeT = TypeVar("TypeT")
TypeC = TypeVar("TypeC")


class _SortDirection(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


class _FilterOperations(str, enum.Enum):
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    LT = "lt"
    GE = "ge"
    LE = "le"
    LIKE = "like"
    ILIKE = "ilike"
    NOT_ILIKE = "not_ilike"
    IN = "in"
    NOT_IN = "not_in"
    ANY = "any"
    NOT_ANY = "not_any"
    MATCH = "match"
    DISTINCT = "distinct"
    PARENT = "parent"
    PARENTS_RECURSIVE = "parents_recursive"
    CHILDREN = "children"
    CHILDREN_RECURSIVE = "children_recursive"


class _FilterPagesize(enum.IntEnum):
    S_BATCH = 15
    M_BATCH = 30
    L_BATCH = 50
    XL_BATCH = 80
    XXL_BATCH = 100


class _Filters(BaseModel, Generic[TypeT]):
    field: TypeT
    operator: _FilterOperations
    value: Any


class _Sorts(BaseModel, Generic[TypeT]):
    field: TypeT
    direction: _SortDirection


class Pagination(BaseModel):
    page_num: Optional[int] = Field(None, gt=0)
    page_offset: Optional[int] = Field(None, ge=0, le=100)
    page_size: _FilterPagesize

    @model_validator(mode="before")
    @classmethod
    def root_validate(  # pylint: disable=no-self-argument
        cls, values: Any
    ) -> Any:
        page_num = values.get("page_num")
        page_offset = values.get("page_offset")

        if all((page_num is not None, page_offset is not None)):
            raise ValueError(
                "'page_num' and 'page_offset' cannot be used together"
            )
        elif (page_num is not None) or (page_offset is not None):
            return values

        raise ValueError(
            "'page_num' or 'page_offset' are missing. "
            "One of these attributes shoud be used"
        )


class BaseSearch(BaseModel):
    pagination: Optional[Pagination] = None

    @model_validator(mode="before")
    @classmethod
    def root_validate(  # pylint: disable=no-self-argument
        cls, values: Any
    ) -> Any:
        if not values.get("pagination"):
            values["pagination"] = Pagination(page_num=1, page_size=15)
        return values


class _BadgerdocSearch(BaseSearch, Generic[TypeT]):
    filters: Optional[List[_Filters[TypeT]]] = None
    sorting: Optional[List[_Sorts[TypeT]]] = None


class PaginationOut(BaseModel):
    page_num: Optional[int] = Field(None, gt=0)
    page_offset: Optional[int] = Field(None, ge=0)
    page_size: _FilterPagesize
    min_pages_left: int
    total: int
    has_more: bool


class Page(BaseModel, Generic[TypeC]):
    pagination: PaginationOut
    data: Sequence[TypeC]

    @field_validator("data", mode="before")
    @classmethod
    def custom_validator(  # pylint: disable=no-self-argument
        cls, v: Any
    ) -> Any:
        """Custom validator applied to data in case of using 'distinct'
        statement and getting result as 'sqlalchemy.util._collections.result'
        but not as model class object
        --------------------------
        Consider this table User:

        id | first_name | last_name
        1  | Adam       | Jensen
        2  | Sam        | Fisher
        3  | Marcus     | Fenix
        4  | Sam        | Serious

        with 'SELECT DISTINCT first_name FROM user'
        (DISTINCT with one column) we'll get list of tuples:
        [('Adam',), ('Sam',), ('Marcus')],
        but we convert it into just list of elements:
        [('Adam',), ('Sam',), ('Marcus')] -> ['Adam', 'Sam', 'Marcus']


        with 'SELECT DISTINCT id, first_name FROM user'
        (DISTINCT with two columns) we'll get list of tuples:
        [(1, 'Adam',), (2, 'Sam',), (3, 'Marcus'), (4, 'Sam')],
        and we convert it to dicts for readability purposes:
        [(1, 'Adam',), (2, 'Sam',), (3, 'Marcus'), (4, 'Sam')] ->
        [
            { "id": 1, "name": "Adam"},
            { "id": 2, "name": "Sam"},
            { "id": 3, "name": "Marcus"},
            { "id": 4, "name": "Sam"},
        ]
        """

        if v and isinstance(v[0], tuple):
            data_element = v[0]

            if len(data_element) == 1:
                data_itself = [x[0] for x in v]
            elif len(data_element) > 1:
                data_itself = [x._asdict() for x in v]

            v = data_itself

        return v


def create_filter_model(
    model: Type[DeclarativeMeta],
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
) -> Type[_BadgerdocSearch]:  # type: ignore
    enum_orm_fields = get_enum_from_orm(
        model, exclude=exclude, include=include
    )
    return _BadgerdocSearch[enum_orm_fields]  # type: ignore
