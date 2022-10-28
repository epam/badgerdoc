from datetime import datetime
from typing import List, Union
from uuid import UUID

from src.db import StatusEnum


def create_expected_models(
    latest: bool,
    version: int,
    basement_id: str = None,
    training_id: str = None,
    categories: List[str] = None,
    created_by: Union[UUID, str] = None,
    model_id: str = None,
    status: StatusEnum = None,
    tenant: str = None,
    name: str = None,
) -> dict:
    return {
        "basement": basement_id,
        "categories": categories,
        "configuration_path": None,
        "created_by": created_by,
        "data_path": None,
        "id": model_id,
        "latest": latest,
        "name": name,
        "score": None,
        "status": status,
        "tenant": tenant,
        "training_id": training_id,
        "type": None,
        "version": version,
    }


def row_to_dict(row) -> dict:
    if hasattr(row, "__table__"):
        return {
            column.key: (
                row.__getattribute__(column.key).isoformat()
                if isinstance(row.__getattribute__(column.key), datetime)
                else row.__getattribute__(column.key)
            )
            for column in row.__table__.columns
            if column.key != "_sa_instance_state"
        }
    return {
        key: (value.isoformat() if isinstance(value, datetime) else value)
        for key, value in row.__dict__.items()
        if key != "_sa_instance_state"
    }


def delete_date_field(entities: list, date_field_name: str) -> None:
    for entity in entities:
        del entity[date_field_name]
