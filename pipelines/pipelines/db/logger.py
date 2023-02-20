import datetime

from sqlalchemy import event, insert
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper

import pipelines.db.models as models
import pipelines.db.service as service
import pipelines.pipeline_runner as runner
import pipelines.schemas as schemas


def create_log(event_type: str, entity: models.Table) -> schemas.Log:
    """Return log with the given entity.

    :param event_type: Type of event.
    :param entity: Entity to log.
    :return: Log with the given entity.
    """
    return schemas.Log(
        entity=schemas.Entity.entity_type(entity),
        event_type=event_type,
        data=entity.as_dict(True),
    )


@event.listens_for(models.Pipeline, "after_insert")
@event.listens_for(models.PipelineExecutionTask, "after_insert")
@event.listens_for(models.ExecutionStep, "after_insert")
def log_after_insert(
    mapper: Mapper, connection: Connection, target: models.Table
) -> None:
    """Listen for the insert event and log to MainEventLog."""
    log_ = create_log(schemas.Event.INS, target).dict()
    stmt = insert(models.MainEventLog).values(
        runner_id=runner.runner_id, event=log_
    )
    connection.execute(stmt)


@event.listens_for(models.Pipeline, "after_delete")
@event.listens_for(models.PipelineExecutionTask, "after_delete")
@event.listens_for(models.ExecutionStep, "after_delete")
def log_after_delete(
    mapper: Mapper, connection: Connection, target: models.Table
) -> None:
    """Listen for the insert event and log to MainEventLog."""
    log_ = create_log(schemas.Event.DEL, target).dict()
    stmt = insert(models.MainEventLog).values(
        runner_id=runner.runner_id, event=log_
    )
    connection.execute(stmt)


@event.listens_for(service.LocalSession, "after_bulk_update")
def log_after_update(update_context) -> None:  # type: ignore
    """Listen for the update event and log to MainEventLog."""
    entity = next(iter(update_context.values)).class_.__name__
    if entity == schemas.Entity.HEART:
        return
    data = {
        k.key: v.isoformat() if isinstance(v, datetime.datetime) else v
        for k, v in update_context.values.items()
    }
    log_ = schemas.Log(
        entity=entity, event_type=schemas.Event.UPD, data=data
    ).dict()
    stmt = insert(models.MainEventLog).values(
        runner_id=runner.runner_id, event=log_
    )
    update_context.session.execute(stmt)
