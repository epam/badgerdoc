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


def get_test_db_url(main_db_url: str) -> str:
    """
    Takes main database url and returns test database url.

    Example:
    postgresql+psycopg2://admin:admin@host:5432/service_name ->
    postgresql+psycopg2://admin:admin@host:5432/test_db
    """
    main_db_url_split = main_db_url.split("/")
    main_db_url_split[-1] = 'test_db'
    result = "/".join(main_db_url_split)
    return result
