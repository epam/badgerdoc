from typing import List, Optional, Tuple

from sqlalchemy.orm import Query, Session

from src import schema
from src.db import models


def session_scope() -> Session:
    """Provide a transactional scope around a series of operations."""
    session = models.SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_task_by_execution_id(
    task_id: int, session: Session
) -> Optional[models.DbPreprocessingTask]:
    return (  # type: ignore
        session.query(models.DbPreprocessingTask)
        .filter(models.DbPreprocessingTask.execution_id == task_id)
        .first()
    )


def update_task(
    execution_id: int, status: schema.StatusForUpdate, session: Session
) -> None:
    query: Query = session.query(models.DbPreprocessingTask).filter(
        models.DbPreprocessingTask.execution_id == execution_id
    )
    query.update(
        {models.DbPreprocessingTask.status: status},
        synchronize_session="fetch",
    )
    session.commit()


def check_preprocessing_complete(
    file_id: int, batch_id: str, session: Session
) -> Tuple[bool, schema.Status]:
    query: Query = session.query(models.DbPreprocessingTask).filter(
        models.DbPreprocessingTask.file_id == file_id,
        models.DbPreprocessingTask.batch_id == batch_id,
    )
    tasks_statuses: List[schema.Status] = [task.status for task in query]
    finished = all(
        [
            status in (schema.Status.DONE, schema.Status.FAIL)
            for status in tasks_statuses
        ]
    )

    if not finished:
        return finished, schema.Status.RUN

    file_status: schema.Status = schema.Status.DONE
    if not all([status == schema.Status.DONE for status in tasks_statuses]):
        file_status = schema.Status.FAIL

    return finished, file_status
