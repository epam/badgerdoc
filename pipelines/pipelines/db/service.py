import asyncio
import datetime
from typing import Any, Callable, Dict, Generator, List, Optional, Type, Union

import pipelines.db.models as dbm
from aiokafka import AIOKafkaProducer
from pipelines import config, execution, log, schemas
from pydantic import AnyUrl
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = log.get_logger(__file__)

engine = create_engine(
    config.DB_URI,
    pool_size=config.POOL_SIZE,
    pool_use_lifo=True,
    pool_pre_ping=True,
)
LocalSession = sessionmaker(bind=engine, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    """Get session to work with the db."""
    session = LocalSession()
    try:
        yield session
    finally:
        session.close()


def run_in_session(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Execute function that requires session as first arg."""
    session = LocalSession()
    try:
        return fn(session, *args, **kwargs)
    finally:
        session.close()


def _add_instances(
    session: Session, instances: dbm.TablesList
) -> List[Union[int, str]]:
    """Add instances to the db.

    :param session: DB session.
    :param instances: List of instances.
    :return: List of instances' ids.
    """
    session.add_all(instances)
    session.flush()
    ids = [instance.id for instance in instances]
    session.commit()
    return ids


def _add_instance(session: Session, instance: dbm.Table) -> Union[int, str]:
    """Add instance to the db.

    :param session: DB session.
    :param instance: Instance.
    :return: Id of instance.
    """
    return _add_instances(session, [instance])[0]


add_pipeline = add_step = add_task = add_heartbeat = _add_instance
add_pipelines = add_steps = add_tasks = _add_instances


def get_all_table_instances(session: Session, table: dbm.TableType) -> dbm.TablesList:
    """Get list of all table instances from the db.

    :param session: DB session.
    :param table: Table by which to search.
    :return: List of all table instances.
    """
    return session.query(table).all()  # type: ignore


def get_table_instance_by_id(
    session: Session, table: dbm.TableType, ident: int
) -> Optional[dbm.Table]:
    """Get instance from the table by its id.

    :param session: DB session.
    :param table: Table by which to search.
    :param ident: Instance id.
    :return: Table instance if found.
    """
    return session.query(table).get(ident)  # type: ignore


def get_pipelines(
    session: Session,
    name: Optional[str] = None,
    version: Optional[int] = None,
    original_pipeline_id: Optional[int] = None,
) -> List[dbm.Pipeline]:
    """Get pipeline list from the db by its name, version or/and
    original pipeline id.

    :param session: DB session.
    :param name: Pipeline name. All if not provided.
    :param version: Version of the pipeline. All if not provided.
    :param original_pipeline_id: Id of base pipeline. All if not provided.
    :return: Pipelines list.
    """
    query = session.query(dbm.Pipeline)
    if name is not None:
        query = query.filter_by(name=name)
    if version is not None:
        query = query.filter_by(version=version)
    if original_pipeline_id is not None:
        query = query.filter_by(original_pipeline_id=original_pipeline_id)
    return query.all()  # type: ignore


def get_task(session: Session, name: str) -> Optional[dbm.PipelineExecutionTask]:
    """Get task by its name. Latest if multiple tasks found.

    :param session: DB session.
    :param name: Task name.
    :return: Tasks list.
    """
    task = (
        session.query(dbm.PipelineExecutionTask)
        .filter_by(name=name)
        .order_by(dbm.PipelineExecutionTask.id.desc())
        .first()
    )
    return task  # type: ignore


def get_task_job_id(session: Session, task_id: int) -> Optional[int]:
    """Get task job_id.

    :param session: DB session.
    :param task_id: Task id.
    :return: Task job_id if found.
    """
    task = get_table_instance_by_id(session, dbm.PipelineExecutionTask, task_id)
    return task.job_id if task else None


def get_webhook(session: Session, task_id: int) -> Optional[str]:
    """Get webhook by task id.

    :param session: DB session.
    :param task_id: Task id.
    :return: webhook
    """
    task = get_table_instance_by_id(session, dbm.PipelineExecutionTask, task_id)
    return task.webhook if task else None


def get_step_by_step_and_task_id(
    session: Session, task_id: int, step_id: str, status: Optional[str] = None
) -> Optional[dbm.ExecutionStep]:
    """Get Execution Step by its step_id (uuid) and tasks' id.

    :param session: DB session.
    :param task_id: Step task_id.
    :param step_id: Step id.
    :param status: Status to filter by.
    :return: Desired step.
    """
    statuses = [i.value for i in schemas.Status]
    statuses = [status] if status else statuses
    return (  # type: ignore
        session.query(dbm.ExecutionStep)
        .filter(
            dbm.ExecutionStep.task_id == task_id,
            dbm.ExecutionStep.step_id == step_id,
            dbm.ExecutionStep.status.in_(statuses)
            | (dbm.ExecutionStep.status == None),  # noqa: E711
        )
        .first()
    )


def delete_instances(
    session: Session,
    objs: dbm.TablesList,
) -> None:
    """Delete instances from the db.

    :param session: DB session.
    :param objs: List of instances to delete.
    """
    for obj in objs:
        session.delete(obj)
    session.commit()


def update_table_instance_fields(
    session: Session,
    table: dbm.TableType,
    id_: Union[int, str],
    args: Dict[str, Any],
) -> None:
    """Update table instances fields.

    :param session: DB session.
    :param table: Model type.
    :param id_: Instance id.
    :param args: Args to update.
    """
    session.query(table).filter(table.id == id_).update(args, synchronize_session=False)
    session.commit()


def update_status(
    session: Session,
    table: Type[Union[dbm.PipelineExecutionTask, dbm.ExecutionStep]],
    id_: int,
    status_: str,
) -> None:
    """Update status of instance.

    :param session: DB session.
    :param table: Model type.
    :param id_: Instance id.
    :param status_: New instance's status.
    """
    update_table_instance_fields(session, table, id_, {table.status: status_})


def update_statuses(
    session: Session,
    table: Type[Union[dbm.PipelineExecutionTask, dbm.ExecutionStep]],
    ids: List[int],
    status_: str,
) -> None:
    """Update instances statuses.

    :param session: DB session.
    :param table: Model type.
    :param ids: List of instances ids.
    :param status_: New instances' status.
    """
    for id_ in ids:
        update_status(session, table, id_, status_)


def get_pending_tasks(
    session: Session, limit: int = 20
) -> List[dbm.PipelineExecutionTask]:
    """Get pending tasks with no runner_id

    :param session: DB session.
    :param limit: limit for sql query
    :return: Desired list of tasks.
    """
    return (  # type: ignore
        session.query(dbm.PipelineExecutionTask)
        .filter(
            dbm.PipelineExecutionTask.status == schemas.Status.PEND,
            dbm.PipelineExecutionTask.runner_id.is_(None),
        )
        .order_by(dbm.PipelineExecutionTask.date)
        .limit(limit)
        .with_for_update()
        .all()
    )


def update_task_in_lock(session: Session, task_id: int, runner_id: str) -> None:
    """Update task runner_id with 'for update' statement.

    :param session: DB session.
    :param task_id: Task id to update.
    :param runner_id: New runner_id for the task.
    """
    session.query(dbm.PipelineExecutionTask).filter(
        dbm.PipelineExecutionTask.id == task_id
    ).with_for_update(skip_locked=True).update(
        {dbm.PipelineExecutionTask.runner_id: runner_id}
    )
    session.commit()


def get_not_finished_tasks(
    session: Session, runner_id: str
) -> List[dbm.PipelineExecutionTask]:
    """Get running or pending pipeline tasks with the given runner_id.

    :param session: DB session.
    :param runner_id: Runner_id by which to search.
    :return: Desired list of tasks.
    """
    return (  # type: ignore
        session.query(dbm.PipelineExecutionTask)
        .filter(
            dbm.PipelineExecutionTask.status.in_(
                [schemas.Status.PEND, schemas.Status.RUN]
            ),
            dbm.PipelineExecutionTask.runner_id == runner_id,
        )
        .all()
    )


def get_heartbeat(session: Session, id_: str) -> Optional[dbm.ExecutorHeartbeat]:
    """Return heartbeat with the given id.

    :param session: DB session.
    :param id_: Id of heartbeat.
    :return: Desired heartbeat.
    """
    return (  # type: ignore
        session.query(dbm.ExecutorHeartbeat)
        .filter(dbm.ExecutorHeartbeat.id == id_)
        .first()
    )


def get_expired_heartbeats(
    session: Session, effective_date: datetime.datetime
) -> List[dbm.ExecutorHeartbeat]:
    """Get expired heartbeats, whose time less than effective_time.

    :param session: DB session.
    :param effective_date: Date by which heartbeats are considered expired.
    :return: Desired heartbeats list.
    """
    return (  # type: ignore
        session.query(dbm.ExecutorHeartbeat)
        .filter(dbm.ExecutorHeartbeat.last_heartbeat <= effective_date)
        .all()
    )


def update_heartbeat_timestamp(session: Session, id_: str) -> None:
    """Update heartbeat last_heartbeat with the current time.

    :param session: DB session.
    :param id_: Heartbeat id.
    """
    args = {dbm.ExecutorHeartbeat.last_heartbeat: datetime.datetime.utcnow()}
    update_table_instance_fields(session, dbm.ExecutorHeartbeat, id_, args)


def change_task_runner_id_status_in_lock(session: Session, id_: int) -> None:
    """Remove runner_id, change status to Pending with 'for update' statement.

    :param session: DB session.
    :param id_: Task id.
    """
    table = dbm.PipelineExecutionTask
    args = {table.runner_id: None, table.status: schemas.Status.PEND}
    session.query(table).filter(table.id == id_).with_for_update(
        skip_locked=True
    ).update(args)
    session.commit()


async def initialize_execution(
    session: Session,
    pipeline: dbm.Pipeline,
    arg: Dict[str, Any],
    producer: AIOKafkaProducer,
    job_id: Optional[int] = None,
    task_name: Optional[str] = None,
    webhook: Optional[AnyUrl] = None,
    tenant: Optional[str] = None,
) -> int:
    """Initialize and add to the db task and steps for pipeline execution.

    :param session: DB session
    :param pipeline: Pipeline model.
    :param arg: Initial args for upmost execution steps.
    :param producer: Kafka producer
    :param job_id: Task's job_id.
    :param task_name: Human readable name of task. UUID if None.
    :param webhook: link for response to Jobs service
    :param tenant: user's tenant
    :return: Created task's id.
    """
    pipeline_ = execution.Pipeline.from_orm(pipeline)
    ids = pipeline_.get_ids()
    names = pipeline_.get_model_ids()
    upmost_ids = [step.id for step in pipeline_.steps]  # High level step ids.
    task = dbm.PipelineExecutionTask(
        name=task_name,
        pipeline=pipeline,
        status=schemas.Status.PEND,
        job_id=job_id,
        webhook=webhook,
    )
    steps = []
    for id_, name in zip(ids, names):
        arg_ = arg if id_ in upmost_ids else None
        steps.append(
            dbm.ExecutionStep(
                task=task,
                name=name,
                step_id=id_,
                init_args=arg_,
                status=schemas.Status.PEND,
                parent_step=await get_step_parent(id_, ids),
                tenant=tenant,
            )
        )
    task_id = add_task(session, task)
    add_steps(session, steps)
    new_task = execution.PipelineTask.from_orm(task)
    asyncio.create_task(new_task.start(producer))
    return task_id  # type: ignore


async def get_step_parent(step_id: str, ids: Dict[str, List[str]]) -> Optional[str]:
    """
    Finds if step has any dependant steps
    """
    for parent, child in ids.items():
        if step_id in child:
            return parent
    return None


def get_job_status_if_changed(
    session: Session, job_id: int, task_status: Union[schemas.Status, str]
) -> Optional[schemas.JobStatus]:
    """Returns current status of the job if it has changed and
    None if the status is the same."""

    def count_tasks_with_status(status: schemas.Status) -> int:
        return len([t.status for t in tasks if t.status == status])

    tasks = (
        session.query(dbm.PipelineExecutionTask)
        .filter(dbm.PipelineExecutionTask.job_id == job_id)
        .order_by(dbm.PipelineExecutionTask.date)
        .all()
    )

    failed_tasks = count_tasks_with_status(schemas.Status.FAIL)
    if failed_tasks > 0:
        if failed_tasks == 1 and task_status == schemas.Status.FAIL:
            return schemas.JobStatus.FAIL
        return None

    done_tasks = count_tasks_with_status(schemas.Status.DONE)
    if len(tasks) == done_tasks:
        return schemas.JobStatus.DONE

    running_tasks = count_tasks_with_status(schemas.Status.RUN)
    if running_tasks == 1 and done_tasks == 0:
        return schemas.JobStatus.RUN

    return None


def is_task_passed(session: Session, task_id: int) -> Optional[bool]:
    """Check if task is failed by its steps.

    :param session: DB session.
    :param task_id: Task id to check.
    :return: True if failed.
    """
    task = (
        session.query(dbm.PipelineExecutionTask)
        .filter(dbm.PipelineExecutionTask.id == task_id)
        .first()
    )
    if task is None:
        return None
    for step in task.steps:
        if step.status == "Failed":
            return False
    return True


def get_step_result_by_step_and_task_id(
    session: Session, task_id: int, step_id: str
) -> Optional[Dict[str, Any]]:
    """Get result of the step.

    :param session: DB session.
    :param task_id: Task id of step.
    :param step_id: Step_id (uuid).
    :return: Result of the step. None if step not found.
    """
    step = (
        session.query(dbm.ExecutionStep)
        .filter(
            dbm.ExecutionStep.task_id == task_id,
            dbm.ExecutionStep.step_id == step_id,
        )
        .first()
    )
    return step.result if step else None


def process_step_startup(
    session: Session, step_db_id: int, init_args: Dict[str, Any]
) -> None:
    """Process step startup by updating its status and init_args.

    :param session: DB session.
    :param step_db_id: Step id.
    :param init_args: Initial args of the step execution.
    :return:
    """
    update_table_instance_fields(
        session,
        dbm.ExecutionStep,
        step_db_id,
        {
            dbm.ExecutionStep.init_args: init_args,
            dbm.ExecutionStep.status: schemas.Status.RUN,
        },
    )


def process_step_completion(
    session: Session,
    step_db_id: int,
    status: str,
    result: Optional[Dict[str, Any]],
) -> None:
    """Perform step completion by updating its status and result.
    Delete if result is None and status is DONE.

    :param session: DB session.
    :param step_db_id: Step id.
    :param status: Status of step execution.
    :param result: Result of step execution.
    """
    if result is None and status == schemas.Status.DONE:
        session.query(dbm.ExecutionStep).filter(
            dbm.ExecutionStep.id == step_db_id
        ).delete()
        session.commit()
        return

    update_table_instance_fields(
        session,
        dbm.ExecutionStep,
        step_db_id,
        {dbm.ExecutionStep.status: status, dbm.ExecutionStep.result: result},
    )


def get_steps_number_by_job_id(
    session: Session,
    job_id: int,
    step_status: Optional[schemas.Status] = None,
) -> int:
    """Counts the number of steps with 'job_id' and 'step_status'.
    None 'step_status' means all steps."""
    query = session.query(dbm.ExecutionStep)
    query = query.join(
        dbm.PipelineExecutionTask,
        dbm.PipelineExecutionTask.id == dbm.ExecutionStep.task_id,
    )
    query = query.filter(dbm.PipelineExecutionTask.job_id == job_id)
    if step_status is not None:
        query = query.filter(
            dbm.ExecutionStep.status == step_status,
        )
    return query.count()  # type: ignore


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
