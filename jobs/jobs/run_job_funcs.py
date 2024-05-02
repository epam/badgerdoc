from typing import Optional

import fastapi
from fastapi import HTTPException
from sqlalchemy.orm import Session

import jobs.db_service as db_service
import jobs.models as dbm
import jobs.schemas as schemas
import jobs.utils as utils


async def run_extraction_job(
    db: Session,
    job_to_run: dbm.CombinedJob,
    current_tenant: str,
    jw_token: str,
) -> Optional[fastapi.HTTPException]:
    """Runs ExtractionJob - creates init_args
    and sends it to the Pipeline Manager"""

    if isinstance(
        job_to_run.pipeline_id, str
    ) and not job_to_run.pipeline_id.endswith(":airflow"):
        raise HTTPException(
            status_code=400,
            detail="Wrong pipeline value.",
        )

    db_service.update_job_mode(db, job_to_run, schemas.JobMode.Automatic)
    converted_files_data = utils.convert_files_data_for_inference(
        all_files_data=job_to_run.all_files_data,
        job_id=job_to_run.id,
        output_bucket=current_tenant,
    )

    await utils.execute_pipeline(
        pipeline_id=job_to_run.pipeline_id,
        job_id=job_to_run.id,
        files_data=converted_files_data,
        current_tenant=current_tenant,
        jw_token=jw_token,
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

    await utils.execute_in_annotation_microservice(
        created_job=job_to_run,
        jw_token=jw_token,
        current_tenant=current_tenant,
    )
    return None
