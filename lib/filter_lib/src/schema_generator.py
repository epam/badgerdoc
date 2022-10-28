import enum
from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar

from pydantic import BaseModel, Field, root_validator
from pydantic.generics import GenericModel
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


class _FilterPagesize(enum.IntEnum):
    S_BATCH = 15
    M_BATCH = 30
    L_BATCH = 50
    XL_BATCH = 80
    XXL_BATCH = 100


class _Filters(GenericModel, Generic[TypeT]):
    field: TypeT
    operator: _FilterOperations
    value: Any


class _Sorts(GenericModel, Generic[TypeT]):
    field: TypeT
    direction: _SortDirection


class Pagination(BaseModel):
    page_num: int = Field(1, gt=0)
    page_size: _FilterPagesize


class BaseSearch(BaseModel):
    pagination: Optional[Pagination]

    @root_validator
    def root_validate(  # pylint: disable=no-self-argument
        cls, values: Any
    ) -> Any:
        if not values.get("pagination"):
            values["pagination"] = Pagination(page_num=1, page_size=15)
        return values


class _BadgerdocSearch(GenericModel, Generic[TypeT], BaseSearch):
    filters: Optional[List[_Filters[TypeT]]]
    sorting: Optional[List[_Sorts[TypeT]]]


class PaginationOut(Pagination):
    min_pages_left: int
    total: int
    has_more: bool


class Page(GenericModel, Generic[TypeC], BaseModel):
    pagination: PaginationOut
    data: Sequence[TypeC]


def create_filter_model(
    model: Type[DeclarativeMeta], exclude: Optional[List[str]] = None
) -> Type[_BadgerdocSearch]:  # type: ignore
    enum_orm_fields = get_enum_from_orm(model, exclude=exclude)
    return _BadgerdocSearch[enum_orm_fields]  # type: ignore
