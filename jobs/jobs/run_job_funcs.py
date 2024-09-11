import logging
from typing import Optional

import fastapi
from sqlalchemy.orm import Session

import jobs.db_service as db_service
import jobs.models as dbm
import jobs.schemas as schemas
import jobs.utils as utils

logger = logging.getLogger(__name__)


async def run_extraction_job(
    db: Session,
    job_to_run: dbm.CombinedJob,
    current_tenant: str,
    jw_token: str,
) -> Optional[fastapi.HTTPException]:
    """Runs ExtractionJob - creates init_args
    and sends it to the Pipeline Manager"""

    db_service.update_job_mode(db, job_to_run, schemas.JobMode.Automatic)
    converted_files_data = utils.convert_files_data_for_inference(
        all_files_data=job_to_run.all_files_data,
        job_id=job_to_run.id,
        output_bucket=current_tenant,
    )
    converted_previous_jobs_data = (
        await utils.convert_previous_jobs_for_inference(
            job_ids=job_to_run.previous_jobs,
            session=db,
            current_tenant=current_tenant,
            jw_token=jw_token,
        )
    )

    logger.info(
        "Starting external pipeline %s for job %s of %s tenant, %s engine",
        job_to_run.pipeline_id,
        job_to_run.id,
        current_tenant,
        job_to_run.pipeline_engine,
    )

    datasets = []
    if job_to_run.datasets:
        datasets_resp = await utils.search_datasets_by_ids(
            datasets_ids=job_to_run.datasets,
            current_tenant=current_tenant,
            jw_token=jw_token,
        )
        datasets = [
            {"id": d["id"], "name": d["name"]} for d in datasets_resp["data"]
        ]

    await utils.execute_external_pipeline(
        pipeline_id=job_to_run.pipeline_id,
        pipeline_engine=job_to_run.pipeline_engine,
        job_id=job_to_run.id,
        previous_jobs_data=converted_previous_jobs_data,
        files_data=converted_files_data,
        current_tenant=current_tenant,
        datasets=datasets,
        revisions=job_to_run.revisions,
    )

    return None


async def run_annotation_job(
    job_to_run: dbm.CombinedJob,
    current_tenant: str,
    jw_token: str,
    db: Session = fastapi.Depends(db_service.get_session),
    updated_status: schemas.JobMode = schemas.JobMode.Manual,
) -> Optional[fastapi.HTTPException]:
    """Runs AnnotationJob - creates init_args
    and sends it to the Annotation Manager"""
    if not job_to_run.type == schemas.JobType.ExtractionWithAnnotationJob:
        db_service.update_job_mode(db, job_to_run, updated_status)

    previous_jobs_data = []

    if job_to_run.previous_jobs:
        previous_jobs = db_service.get_jobs_in_db_by_ids(
            db, job_to_run.previous_jobs
        )
        previous_jobs_data = [
            {
                "job_id": p_job.id,
                "files": p_job.files,
                "datasets": p_job.datasets,
            }
            for p_job in previous_jobs
        ]

    await utils.execute_in_annotation_microservice(
        created_job=job_to_run,
        previous_jobs_data=previous_jobs_data,
        jw_token=jw_token,
        current_tenant=current_tenant,
    )
    return None
