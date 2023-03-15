import enum
from typing import List, Optional, Type

from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.properties import ColumnProperty


class TempEnum(str, enum.Enum):
    pass


def _get_model_fields(model: Type[DeclarativeMeta]) -> List[str]:
    mapper: Mapper = inspect(model)
    relations = [
        attr
        for attr in inspect(model).attrs
        if isinstance(attr, RelationshipProperty)
    ]
    relation_fields = [
        rel.key + "." + col.key
        for rel in relations
        for col in rel.entity.local_table._columns
    ]
    fields = [
        attr.key
        for attr in mapper.attrs
        if isinstance(attr, ColumnProperty) and attr.columns
    ]
    fields.extend(relation_fields)
    return fields


def _get_table_name(model: Type[DeclarativeMeta]) -> str:
    name = inspect(model).local_table.name
    return str(name) + "_" + model.__name__


def _exclude_fields(model_fields: List[str], exclude: List[str]) -> List[str]:
    result = [x for x in model_fields if x not in exclude]
    return result


def _create_enum_model(table_name: str, fields: List[str]) -> enum.EnumMeta:
    enum_fields = {key.upper(): key for key in fields}
    model = TempEnum(table_name, enum_fields)  # type: ignore
    return model  # type: ignore


def get_enum_from_orm(
    model: Type[DeclarativeMeta], exclude: Optional[List[str]] = None
) -> enum.EnumMeta:
    orm_fields = _get_model_fields(model)
    table_name = _get_table_name(model)
    if exclude:
        orm_fields = _exclude_fields(orm_fields, exclude=exclude)
    result = _create_enum_model(table_name, orm_fields)
    return result
