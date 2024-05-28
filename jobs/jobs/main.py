import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from filter_lib import Page, form_query, map_request_to_filter, paginate
from sqlalchemy.orm import Session
from sqlalchemy_filters.exceptions import BadFilterFormat
from tenant_dependency import TenantData, get_tenant_info

import jobs.airflow_utils as airflow_utils
import jobs.categories as categories
import jobs.create_job_funcs as create_job_funcs
import jobs.databricks_utils as databricks_utils
import jobs.db_service as db_service
import jobs.models as dbm
import jobs.run_job_funcs as run_job_funcs
import jobs.schemas as schemas
import jobs.utils as utils
from jobs.config import KEYCLOAK_HOST, ROOT_PATH, API_current_version

tenant = get_tenant_info(url=KEYCLOAK_HOST, algorithm="RS256", debug=True)
logger = logging.getLogger(__name__)
AIRFLOW_ENABLED = os.getenv("AIRFLOW_ENABLED", "").lower() == "true"
DATABRICKS_ENABLED = os.getenv("DATABRICKS_ENABLED", "").lower() == "true"

app = FastAPI(
    title="Job Manager",
    root_path=ROOT_PATH,
    version=API_current_version,
    dependencies=[Depends(tenant)],
)

if WEB_CORS := os.getenv("WEB_CORS", ""):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=WEB_CORS.split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )

NO_JOB = "No such job"

check_for_job_owner_in_change_job = (
    False  # Temporarily disabled check for job_owner in change_job endpoint
)


@app.post("/jobs/create_job")
async def create_job(
    job_params: schemas.JobParams,
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db: Session = Depends(db_service.get_session),
    token_data: TenantData = Depends(tenant),
) -> Union[Dict[str, Any], None]:
    """Creates ExtractionJob, AnnotationJob or ExtractionWithAnnotationJob.
    If it is not 'Draft' - runs it"""
    logger.info("Create job with job_params: %s", job_params)
    jw_token = token_data.token

    if job_params.previous_jobs:
        previous_jobs = db_service.get_jobs_in_db_by_ids(
            db, job_params.previous_jobs
        )
        if not previous_jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Jobs with these ids do not exist.",
            )
        job_params.previous_jobs = [j.id for j in previous_jobs]

    if job_params.type == schemas.JobType.ExtractionJob:
        created_extraction_job = await create_job_funcs.create_extraction_job(
            extraction_job_input=job_params,  # type: ignore
            current_tenant=current_tenant,
            db=db,
            jw_token=jw_token,
        )
        if not job_params.is_draft:
            logger.info("Running jobs")
            await run_job_funcs.run_extraction_job(
                db=db,
                job_to_run=created_extraction_job,
                current_tenant=current_tenant,
                jw_token=jw_token,
            )
            await run_job_funcs.run_annotation_job(
                job_to_run=created_extraction_job,
                current_tenant=current_tenant,
                db=db,
                updated_status=schemas.JobMode.Automatic,
                jw_token=jw_token,
            )
        return created_extraction_job.as_dict

    if job_params.type in {
        schemas.JobType.AnnotationJob,
        schemas.JobType.ExtractionWithAnnotationJob,
    }:
        categories_links: List[schemas.CategoryLinkInput] = []
        if job_params.categories:
            categories_ids, categories_links = utils.get_categories_ids(
                job_params.categories
            )
            job_params.categories = categories_ids

        if job_params.type == schemas.JobType.AnnotationJob:
            created_annotation_job = (
                await create_job_funcs.create_annotation_job(
                    annotation_job_input=job_params,  # type: ignore
                    db=db,
                )
            )
            if not job_params.is_draft:
                await run_job_funcs.run_annotation_job(
                    job_to_run=created_annotation_job,
                    current_tenant=current_tenant,
                    db=db,
                    jw_token=jw_token,
                )
            created_job = created_annotation_job.as_dict

        else:
            created_extraction_annotation_job = (
                await create_job_funcs.create_extraction_annotation_job(
                    extraction_annotation_job_input=job_params,  # type: ignore
                    current_tenant=current_tenant,
                    db=db,
                    jw_token=jw_token,
                )
            )
            if not job_params.is_draft:
                await run_job_funcs.run_extraction_job(
                    db=db,
                    job_to_run=created_extraction_annotation_job,
                    current_tenant=current_tenant,
                    jw_token=jw_token,
                )
                await run_job_funcs.run_annotation_job(
                    job_to_run=created_extraction_annotation_job,
                    current_tenant=current_tenant,
                    db=db,
                    updated_status=schemas.JobMode.Automatic,
                    jw_token=jw_token,
                )
            created_job = created_extraction_annotation_job.as_dict

        if categories_links:
            job_id = created_job["id"]
            taxonomy_links = utils.get_taxonomy_links(job_id, categories_links)
            await utils.send_category_taxonomy_link(
                current_tenant, jw_token, taxonomy_links
            )
        return created_job

    if job_params.type == schemas.JobType.ImportJob:
        new_import_job = db_service.create_import_job(db, job_params)  # type: ignore  # noqa: E501
        return new_import_job.as_dict

    return None


@app.post("/start/{job_id}")
async def run_job(
    job_id: int,
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db: Session = Depends(db_service.get_session),
    token_data: TenantData = Depends(tenant),
) -> Union[Dict[str, Any], HTTPException]:
    """Runs any type of Job"""
    jw_token = token_data.token
    job_to_run = db_service.get_job_in_db_by_id(db, job_id)
    if not job_to_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job with this id does not exist.",
        )

    if job_to_run.status != schemas.Status.draft:
        if not (
            job_to_run.type == schemas.JobType.ExtractionWithAnnotationJob
            and job_to_run.status == schemas.Status.ready_for_annotation
        ):
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="You can run only Job with a status 'Draft' or "
                "ExtractionWithAnnotationJob with finished Automatic part",
            )

    if job_to_run.type == schemas.JobType.ExtractionJob:
        await run_job_funcs.run_extraction_job(
            db=db,
            job_to_run=job_to_run,
            current_tenant=current_tenant,
            jw_token=jw_token,
        )

    if job_to_run.type == schemas.JobType.AnnotationJob:
        await run_job_funcs.run_annotation_job(
            job_to_run=job_to_run,
            current_tenant=current_tenant,
            db=db,
            jw_token=jw_token,
        )

    if job_to_run.type == schemas.JobType.ExtractionWithAnnotationJob:
        if job_to_run.status == schemas.Status.draft:
            await run_job_funcs.run_extraction_job(
                db=db,
                job_to_run=job_to_run,
                current_tenant=current_tenant,
                jw_token=jw_token,
            )  # Running Automatic Extraction part
        if job_to_run.status == schemas.Status.ready_for_annotation:
            await run_job_funcs.run_annotation_job(
                job_to_run=job_to_run,
                current_tenant=current_tenant,
                db=db,
                jw_token=jw_token,
            )  # Running Manual Annotation part

    db_service.update_job_status(db, job_to_run, schemas.Status.pending)

    return job_to_run.as_dict


@app.put("/jobs/{job_id}")
async def change_job(
    job_id: int,
    new_job_params: schemas.JobParamsToChange,
    token_data: TenantData = Depends(tenant),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db: Session = Depends(db_service.get_session),
) -> Union[Dict[str, Any], HTTPException]:
    """Provides an ability to change any value
    of any field of any Job in the database"""

    logger.info("Start job %s update with params %s", job_id, new_job_params)
    job_to_change = db_service.get_job_in_db_by_id(db, job_id, with_lock=True)
    if not job_to_change:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job with this id does not exist.",
        )

    if check_for_job_owner_in_change_job:
        user_id = token_data.user_id
        if (owners := job_to_change.owners) and user_id not in owners:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This user is not "
                "allowed to change the job",
            )

    if (
        new_job_params.type == schemas.JobType.ExtractionWithAnnotationJob
        and job_to_change.type != schemas.JobType.ExtractionJob
    ):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"only {schemas.JobType.ExtractionJob} is allowed to be "
            f"converted to {schemas.JobType.ExtractionWithAnnotationJob}",
        )

    jw_token = token_data.token
    try:
        (
            new_categories_ids,
            new_categories_links,
        ) = await categories.prepare_for_update(
            job_to_change, new_job_params, current_tenant, jw_token
        )
    except NotImplementedError as err:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=str(err)
        ) from err

    if new_categories_ids:
        new_job_params.categories = new_categories_ids

    if job_to_change.type in [
        schemas.JobType.AnnotationJob,
        schemas.JobType.ExtractionWithAnnotationJob,
    ]:
        new_job_params_for_annotation = utils.pick_params_for_annotation(
            new_job_params
        )
        if new_job_params_for_annotation.dict(exclude_defaults=True):
            changed_params = await utils.update_job_in_annotation(
                job_id=job_id,
                new_job_params_for_annotation=new_job_params_for_annotation,
                current_tenant=current_tenant,
                jw_token=jw_token,
            )
            for field, value in changed_params.items():
                setattr(new_job_params, field, value)

    is_job_changed = False
    if job_to_change.type == schemas.JobType.ExtractionWithAnnotationJob:
        if (
            job_to_change.mode == schemas.JobMode.Automatic
            and new_job_params.status == schemas.Status.finished
        ):
            new_job_params.mode = schemas.JobMode.Manual
            new_job_params.status = schemas.Status.ready_for_annotation
            if job_to_change.start_manual_job_automatically:
                db_service.change_job(db, job_to_change, new_job_params)
                await utils.start_job_in_annotation(
                    job_id, current_tenant, token_data.token
                )
                is_job_changed = True

    if (
        job_to_change.type == schemas.JobType.ExtractionJob
        and new_job_params.type == schemas.JobType.ExtractionWithAnnotationJob
    ):
        new_job_params.mode = schemas.JobMode.Manual
        new_job_params.status = schemas.Status.ready_for_annotation

    if not is_job_changed:
        db_service.change_job(db, job_to_change, new_job_params)

    if new_categories_links:
        taxonomy_links = utils.get_taxonomy_links(job_id, new_categories_links)
        await utils.send_category_taxonomy_link(
            current_tenant, jw_token, taxonomy_links
        )
    return job_to_change.as_dict


@app.get("/jobs")
async def get_all_jobs(
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db: Session = Depends(db_service.get_session),
) -> List[Dict[str, Any]]:
    """Returns a list of all jobs in the database"""
    result = db_service.get_all_jobs(db)
    return result


@app.post("/jobs/search")
async def search_jobs(
    request: dbm.JobFilter,
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db: Session = Depends(db_service.get_session),
) -> Page[Dict[str, Any]]:
    """Returns a list of Jobs in line with filters specified"""

    query = db.query(dbm.CombinedJob)
    filter_args = map_request_to_filter(request.dict(), "CombinedJob")
    try:
        query, pag = form_query(filter_args, query)
    except BadFilterFormat as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{e}",
        )
    return paginate([element for element in query], pag)


@app.get("/jobs/{job_id}")
async def get_job_by_id(
    job_id: int,
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db: Session = Depends(db_service.get_session),
    token_data: TenantData = Depends(tenant),
) -> Dict[str, Any]:
    """Getting hold on a job in the database by its id"""

    job_needed = db_service.get_job_in_db_by_id(db, job_id)
    if not job_needed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job with this id does not exist.",
        )
    result = await utils.enrich_annotators_with_usernames(
        job_needed, current_tenant, token_data.token
    )

    return {**result.as_dict, "files": result.files_ids}


@app.delete("/jobs/{job_id}")
async def delete_job(
    job_id: int,
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db: Session = Depends(db_service.get_session),
    token_data: TenantData = Depends(tenant),
) -> Union[Dict[str, Any], HTTPException]:
    """Deletes Job instance by its id"""
    jw_token = token_data.token
    job_to_delete = db_service.get_job_in_db_by_id(db, job_id)
    if not job_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job with this id does not exist.",
        )
    db_service.delete_job(db, job_to_delete)
    await utils.delete_taxonomy_link(job_id, current_tenant, jw_token)
    return {"success": f"Job with id={job_id} was deleted"}


@app.get("/metadata")
async def get_metadata(
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> Dict[str, List[str]]:
    """Provides metadata that contains names
    and values of Enum Classes from schemas"""
    return {
        schemas.JobType.__name__: [member.value for member in schemas.JobType],
        schemas.Status.__name__: [member.value for member in schemas.Status],
        schemas.ValidationType.__name__: [
            member.value for member in schemas.ValidationType
        ],
    }


@app.post(
    "/jobs/progress",
    status_code=200,
    response_model=Dict[int, schemas.JobProgress],
)
async def get_jobs_progress(
    job_ids: List[int],
    session: Session = Depends(db_service.get_session),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    token_data: TenantData = Depends(tenant),
) -> Dict[int, Dict[str, int]]:
    jw_token = token_data.token
    progress_tasks = [
        utils.get_job_progress(job_id, session, current_tenant, jw_token)
        for job_id in job_ids
    ]
    jobs_progress = await asyncio.gather(*progress_tasks)
    return {
        job_id: job_progress
        for job_id, job_progress in zip(job_ids, jobs_progress)
        if job_progress is not None
    }


#################################################
#
# Pipelines
#
#################################################


@app.get(
    "/pipelines/support",
    response_model=schemas.PipelineEngineSupport,
    tags=["pipelines"],
)
async def support(
    _: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> schemas.PipelineEngineSupport:
    default_pipelines = {
        "airflow": AIRFLOW_ENABLED,
        "databricks": DATABRICKS_ENABLED,
    }
    pipeline_engines = []
    for pipeline_name, enabled in default_pipelines.items():
        pipeline_engines.append(
            schemas.PipelineEngine(
                name=pipeline_name.capitalize(),
                enabled=enabled,
                resource=f"/pipelines/{pipeline_name}",
            )
        )

    return schemas.PipelineEngineSupport(data=pipeline_engines)


# AIRFLOW


@app.get("/pipelines/airflow", tags=["pipelines", "airflow"])
async def airflow(
    _: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> schemas.Pipelines:
    dags = await airflow_utils.get_dags()
    try:
        return schemas.Pipelines(
            data=[
                schemas.Pipeline(
                    name=dag["dag_id"],
                    id=dag["dag_id"],
                    version=0,
                    type="airflow",
                    date="2024-05-02T11:14:20.506320",
                    meta={},
                    steps=[],
                )
                for dag in dags["dags"]
            ]
        )
    except KeyError:
        logger.exception("Unexpected airflow dags response: %s", dags)
        raise


@app.post(
    "/pipelines/airflow/{pipeline_id}/execute", tags=["pipelines", "airflow"]
)
async def execute_airflow(pipeline_id: str):
    pass


# DataBricks


@app.get("/pipelines/databricks", tags=["pipelines", "databricks"])
async def databricks(
    _: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> schemas.Pipelines:
    pipelines = list(databricks_utils.get_pipelines())
    return schemas.Pipelines(data=pipelines)
