from typing import Dict, Optional, Tuple, Union

from sqlalchemy import desc
from sqlalchemy.orm import Session

from models.db import Basement, Model, Training
from models.schemas import BasementBase, ModelBase, TrainingBase, TrainingUpdate


def is_id_existing(
    session: Session,
    table: Union[Basement, Model, Training],
    instance_id: Union[str, int],
) -> Union[Basement, Model, Training]:
    return session.query(table).filter(table.id == instance_id).all()


def create_instance(
    session: Session,
    table: Union[Basement, Model, Training],
    args: Union[BasementBase, ModelBase, TrainingBase],
    author: str,
    tenant: str,
    model_args: Dict[str, Union[int, bool]] = None,
) -> Union[Basement, Model, Training]:
    args = args.dict()
    if model_args:
        args.update(model_args)
    instance = table(**args, created_by=author, tenant=tenant)
    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance


def get_instance(
    session: Session,
    table: Union[Basement, Model, Training],
    primary_key: Union[int, str, Tuple[str, int]],
) -> Union[Basement, Model, Training, None]:
    instance = session.query(table).get(primary_key)
    return instance


def modify_instance(
    session: Session,
    instance: Union[Basement, Model, Training],
    request: Union[BasementBase, ModelBase, TrainingUpdate],
) -> Union[Basement, Model, Training]:
    for key, value in request:
        if key == "id":
            continue
        if key in ("data_path", "configuration_path") and value:
            setattr(instance, key, dict(value))
            continue
        setattr(instance, key, value)
    session.commit()
    session.refresh(instance)
    return instance


def delete_instance(
    session: Session, instance: Union[Basement, Model, Training]
) -> None:
    session.delete(instance)
    session.commit()


def modify_status(
    session: Session, instance: Model, previous: str, current: str
) -> None:
    if instance.status == previous:
        instance.status = current
        session.commit()


def update_files_keys(
    session: Session,
    instance: Union[Basement, Training],
    key_script: str,
    key_archive: str,
) -> None:
    if key_script:
        instance.key_script = key_script
    if key_archive:
        instance.key_archive = key_archive
    session.commit()


def get_latest_model(session: Session, model_id: str) -> Optional[Model]:
    return (
        session.query(Model)
        .filter(Model.id == model_id, Model.latest == True)  # noqa E712
        .first()
    )


def get_second_latest_model(
    session: Session, model_id: str
) -> Optional[Model]:
    """
    Find second model by desc version
    """
    return (
        session.query(Model)
        .filter(Model.id == model_id)
        .order_by(desc(Model.version))
        .offset(1)
        .first()
    )
