import datetime
from typing import Any, Dict, List, Union

import sqlalchemy
from scheduler import config, unit
from scheduler.db import models
from sqlalchemy import orm

engine = sqlalchemy.create_engine(config.DB_URL, pool_size=int(config.POOL_SIZE))
Session = orm.sessionmaker(bind=engine, expire_on_commit=False)


def add_into_db(session: orm.Session, instance: models.TableType) -> None:
    """Add instance to the db."""
    session.add(instance)


def update_instance_by_id(
    session: orm.Session,
    table: models.TableType,
    id_: Union[int, str],
    args: Dict[str, Any],
) -> None:
    """Update 'args' fields of 'table' instance with id = 'id_'."""
    session.query(table).filter(table.id == id_).update(args)


def get_unit_by_id(session: orm.Session, id_: str) -> models.Unit:
    """Get instance from the Unit table by id."""
    return session.get(models.Unit, id_)


def update_heartbeat_timestamp(session: orm.Session, id_: str) -> None:
    """Update heartbeat 'last_heartbeat' attribute with the current time."""
    args = {models.Heartbeat.last_heartbeat: datetime.datetime.utcnow()}
    update_instance_by_id(session, models.Heartbeat, id_, args)


def get_expired_heartbeats(
    session: orm.Session,
    effective_date: datetime.datetime,
) -> List[models.Heartbeat]:
    """Get expired heartbeats, whose time less than effective_time."""
    return (  # type: ignore
        session.query(models.Heartbeat)
        .filter(models.Heartbeat.last_heartbeat <= effective_date)
        .all()
    )


def get_not_finished_units(session: orm.Session, runner_id: str) -> List[models.Unit]:
    """Get units with statuses 'RECEIVED' and 'IN_PROGRESS'
    with the given runner_id.
    """
    return (  # type: ignore
        session.query(models.Unit)
        .filter(
            models.Unit.status.in_(
                [unit.UnitStatus.RECEIVED, unit.UnitStatus.IN_PROGRESS]
            ),
            models.Unit.runner_id == runner_id,
        )
        .with_for_update()
        .all()
    )


def change_unit_runner_id_in_lock(session: orm.Session, id_: str) -> None:
    """For unit with id = 'id_' remove runner_id,
    change status to 'RECEIVED' with 'for update' statement.
    """
    args = {"runner_id": None, "status": unit.UnitStatus.RECEIVED}
    session.query(models.Unit).filter(models.Unit.id == id_).with_for_update().update(
        args
    )


def delete_instances(session: orm.Session, objs: models.TablesList) -> None:
    """Delete instances from the db."""
    for obj in objs:
        session.delete(obj)


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
