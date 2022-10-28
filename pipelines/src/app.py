import asyncio
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, FastAPI, Header, HTTPException, status
from filter_lib import Page, form_query, map_request_to_filter, paginate
from pydantic import AnyUrl
from sqlalchemy.orm import Session
from sqlalchemy_filters.exceptions import BadFilterFormat
from tenant_dependency import TenantData, get_tenant_info

import src.config as config
import src.db.models as dbm
import src.db.service as service
import src.execution as execution
import src.schemas as schemas
from src.kafka_utils import Kafka
from src.pipeline_runner import run_pipeline

TOKEN = get_tenant_info(url=config.KEYCLOAK_URI, algorithm="RS256")

app = FastAPI(
    title="Pipelines",
    version=config.VERSION,
    root_path=config.ROOT_PATH,
    servers=[{"url": config.ROOT_PATH}],
)

kafka = Kafka()

# Exception messages
NO_PIPELINE = "No such pipeline."
NO_TASK = "No such task."
NO_LATEST_TASK = "No latest task."
NO_JOB = "No such job"


@app.on_event("startup")
async def startup_kafka() -> None:
    kafka.create_topics()

    async def start_pipeline() -> None:
        await kafka.consumer.start()
        await kafka.producer.start()
        await run_pipeline(kafka.consumer, kafka.producer)
        await kafka.consumer.stop()
        await kafka.producer.stop()

    asyncio.create_task(start_pipeline())


@app.post(
    "/pipeline",
    status_code=201,
    response_model=schemas.PipelineOutId,
    tags=["pipelines"],
)
async def add_pipeline(
    pipeline: execution.Pipeline,
    session: Session = Depends(service.get_session),
) -> schemas.PipelineOutId:
    """Add pipeline to DB."""
    if pipeline.meta.original_pipeline_id is None:
        pipeline.check_name(session)
    else:
        pipeline.update_version(session)

    ids_ = pipeline.get_model_ids()
    pipeline.check_valid_ids(ids_)
    pipeline.adjust_pipeline(ids_)

    pipeline_db = pipeline.to_orm()
    pipeline_id = service.add_pipeline(session, pipeline_db)
    if pipeline.meta.original_pipeline_id is None:
        pipeline.update_original_pipeline_id(session, pipeline_id)

    return schemas.PipelineOutId(id=pipeline_id)


@app.get(
    "/pipeline",
    status_code=200,
    response_model=schemas.PipelineOut,
    response_model_exclude_unset=True,
    tags=["pipelines"],
)
async def get_pipeline(
    name: str,
    version: Optional[int] = None,
    session: Session = Depends(service.get_session),
) -> Any:
    """Get latest pipeline from DB by name (and version)."""
    res = service.get_pipelines(session, name, version)
    if res:
        last_pipeline = sorted(res, key=lambda p: p.version)[-1]  # type:ignore
        return last_pipeline.as_dict()
    raise HTTPException(status_code=404, detail=NO_PIPELINE)


@app.get(
    "/pipelines",
    status_code=200,
    response_model=List[schemas.PipelineOut],
    response_model_exclude_unset=True,
    tags=["pipelines"],
)
async def get_pipelines(
    name: Optional[str] = None,
    session: Session = Depends(service.get_session),
) -> Any:
    """Gets all versions of pipeline from the DB.
    If 'name' is not specified, gets all pipelines."""
    if name is not None:
        res = service.get_pipelines(session, name)
    else:
        res = service.get_all_table_instances(session, dbm.Pipeline)
    return [pipeline.as_dict() for pipeline in res]


@app.post(
    "/pipelines/search",
    response_model=Union[Page[schemas.PipelineOut], Page[Any]],
    response_model_exclude_unset=True,
    tags=["pipelines"],
)
def search_pipelines(
    request: dbm.PipelineFilter,
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    session: Session = Depends(service.get_session),
) -> Any:
    """Returns a list of Jobs in line with filters specified"""
    query = session.query(dbm.Pipeline)
    filter_args = map_request_to_filter(request.dict(), "Pipeline")
    try:
        query, pag = form_query(filter_args, query)
    except BadFilterFormat as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{e}",
        )
    return paginate([element for element in query], pag)


@app.delete(
    "/pipelines",
    status_code=200,
    response_model=Dict[str, str],
    tags=["pipelines"],
)
async def delete_pipelines(
    name: str,
    version: Optional[int] = None,
    session: Session = Depends(service.get_session),
) -> Dict[str, str]:
    """Delete pipelines from db by name. All versions if not provided."""
    res = service.get_pipelines(session, name, version)
    if res:
        service.delete_instances(session, res)
        return {"result": "Pipelines has been deleted."}
    raise HTTPException(status_code=404, detail=NO_PIPELINE)


@app.delete(
    "/pipelines/{pipeline_id}",
    status_code=200,
    response_model=Dict[str, str],
    tags=["pipelines"],
)
async def delete_pipeline_by_id(
    pipeline_id: int, session: Session = Depends(service.get_session)
) -> Dict[str, str]:
    """Delete pipeline from db by its id."""
    res = service.get_table_instance_by_id(session, dbm.Pipeline, pipeline_id)
    if res is None:
        raise HTTPException(status_code=404, detail=NO_PIPELINE)
    service.delete_instances(session, [res])
    return {"result": "Pipeline has been deleted."}


@app.get(
    "/pipelines/{pipeline_id}",
    status_code=200,
    response_model=schemas.PipelineOut,
    response_model_exclude_unset=True,
    tags=["pipelines"],
)
async def get_pipeline_by_id(
    pipeline_id: int, session: Session = Depends(service.get_session)
) -> Any:
    """Get pipeline from DB by its id."""
    res = service.get_table_instance_by_id(session, dbm.Pipeline, pipeline_id)
    if res:
        return res.as_dict()
    raise HTTPException(status_code=404, detail=NO_PIPELINE)


@app.get(
    "/pipelines/tasks/{task_id}",
    status_code=200,
    response_model=schemas.PipelineExecutionTaskOut,
    response_model_exclude_unset=True,
    tags=["tasks"],
)
async def get_task_by_id(
    task_id: int, session: Session = Depends(service.get_session)
) -> Any:
    """Get task by its id."""
    res = service.get_table_instance_by_id(
        session, dbm.PipelineExecutionTask, task_id
    )
    if res:
        return res.as_dict()
    raise HTTPException(status_code=404, detail=NO_TASK)


@app.get(
    "/pipelines/{pipeline_id}/task",
    status_code=200,
    response_model=schemas.PipelineExecutionTaskOut,
    response_model_exclude_unset=True,
    tags=["tasks"],
)
async def get_task_by_pipeline_id(
    pipeline_id: int, session: Session = Depends(service.get_session)
) -> Any:
    """Get latest pipeline task by pipeline id."""
    res = service.get_table_instance_by_id(session, dbm.Pipeline, pipeline_id)
    if res is None:
        raise HTTPException(status_code=404, detail=NO_PIPELINE)
    tasks = res.tasks
    if not tasks:
        raise HTTPException(status_code=404, detail=NO_LATEST_TASK)
    return tasks[-1].as_dict()


@app.get(
    "/pipelines/{pipeline_id}/tasks",
    status_code=200,
    response_model=List[schemas.PipelineExecutionTaskOut],
    response_model_exclude_unset=True,
    tags=["tasks"],
)
async def get_tasks_by_pipeline_id(
    pipeline_id: int, session: Session = Depends(service.get_session)
) -> List[Dict[str, Any]]:
    """Get pipeline tasks by pipeline id."""
    res = service.get_table_instance_by_id(session, dbm.Pipeline, pipeline_id)
    if res is None:
        raise HTTPException(status_code=404, detail=NO_PIPELINE)
    return [task.as_dict() for task in res.tasks]


@app.post(
    "/pipelines/{pipeline_id}/execute",
    status_code=200,
    response_model=List[schemas.PipelineExecutionTaskIdOut],
    tags=["execution"],
)
async def execute_pipeline_by_id(
    pipeline_id: int,
    args: List[schemas.InputArguments],
    job_id: Optional[int] = None,
    task_name: Optional[str] = None,
    webhook: Optional[AnyUrl] = None,
    session: Session = Depends(service.get_session),
    x_current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    token: TenantData = Depends(TOKEN),
) -> List[Dict[str, Any]]:
    """Schedule pipeline execution n times for n-given args."""
    res = service.get_table_instance_by_id(session, dbm.Pipeline, pipeline_id)
    if res is None:
        raise HTTPException(status_code=404, detail=NO_PIPELINE)

    task_ids = [
        await service.initialize_execution(
            session=session,
            pipeline=res,
            arg=arg.dict(exclude_unset=True),
            producer=kafka.producer,
            job_id=job_id,
            task_name=task_name,
            webhook=webhook,
            tenant=x_current_tenant,
        )
        for arg in args
    ]

    return [{"id": task_id} for task_id in task_ids]


@app.delete(
    "/pipelines/tasks/{task_id}",
    status_code=200,
    response_model=Dict[str, str],
    tags=["tasks"],
)
async def delete_task(
    task_id: int, session: Session = Depends(service.get_session)
) -> Dict[str, str]:
    """Delete task from db by its id."""
    res = service.get_table_instance_by_id(
        session, dbm.PipelineExecutionTask, task_id
    )
    if res is None:
        raise HTTPException(status_code=404, detail=NO_TASK)
    service.delete_instances(session, [res])
    return {"result": "Task has been deleted."}


@app.get(
    "/pipelines/tasks/{task_id}/steps/",
    status_code=200,
    response_model=List[schemas.ExecutionStepOut],
    response_model_exclude_unset=True,
    tags=["steps"],
)
async def get_task_steps_by_id(
    task_id: int, session: Session = Depends(service.get_session)
) -> List[Dict[str, str]]:
    """Get task steps by task id."""
    res = service.get_table_instance_by_id(
        session, dbm.PipelineExecutionTask, task_id
    )
    if res is None:
        raise HTTPException(status_code=404, detail=NO_TASK)
    return [step.as_dict() for step in res.steps]


@app.get(
    "/jobs/{job_id}/progress",
    status_code=200,
    response_model=schemas.JobProgress,
    tags=["jobs"],
)
async def get_job_progress_by_job_id(
    job_id: int, session: Session = Depends(service.get_session)
) -> Dict[str, int]:
    """Get progress by job id: finished and total steps."""
    total = service.get_steps_number_by_job_id(session, job_id)
    if total == 0:
        raise HTTPException(status_code=404, detail=NO_JOB)
    finished = service.get_steps_number_by_job_id(
        session=session, job_id=job_id, step_status=schemas.Status.DONE
    )
    return {"finished": finished, "total": total}
