import itertools
from typing import Any, Dict, List, Tuple

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

import jobs.db_service as db_service
import jobs.models as dbm
import jobs.schemas as schemas
import jobs.utils as utils
from jobs.schemas import ExtractionJobParams


async def get_all_datasets_and_files_data(
    datasets_tags: List[int],
    files_ids: List[int],
    current_tenant: str,
    jw_token: str,
) -> Tuple[List[Dict[str, Any]], List[int], List[int]]:
    """Gets all the data about datasets and files passed in
    from Assets microservice. Also returns valid dataset tags and valid
    file ids - if they exist in assets"""
    get_datasets_data_response = await utils.get_files_data_from_datasets(
        datasets_data=datasets_tags,
        current_tenant=current_tenant,
        jw_token=jw_token,
    )
    files_data_from_datasets, valid_dataset_tags = get_datasets_data_response

    get_files_data_response = await utils.get_files_data_from_separate_files(
        separate_files_ids=files_ids,
        current_tenant=current_tenant,
        jw_token=jw_token,
    )
    (
        files_data_from_separate_files,
        valid_separate_files_uuids,
    ) = get_files_data_response

    files_data = files_data_from_datasets + files_data_from_separate_files
    return files_data, valid_dataset_tags, valid_separate_files_uuids


# noinspection PyUnreachableCode
async def create_extraction_job(
    extraction_job_input: ExtractionJobParams,
    current_tenant: str,
    jw_token: str,
    db: Session = Depends(db_service.get_session),
) -> dbm.CombinedJob:
    """Creates new ExtractionJob and saves it in the database"""

    if False:
        # old pipelines service
        pipeline_instance = await utils.get_pipeline_instance_by_its_name(
            pipeline_name=extraction_job_input.pipeline_name,
            current_tenant=current_tenant,
            jw_token=jw_token,
            pipeline_version=extraction_job_input.pipeline_version,
        )

        pipeline_id = (
            extraction_job_input.pipeline_name
            if extraction_job_input.pipeline_name.endswith(":airflow")
            else pipeline_instance.get("id")
        )

        pipeline_categories = pipeline_instance.get("meta", {}).get(
            "categories", []
        )

    else:
        pipeline_id = extraction_job_input.pipeline_id
        pipeline_engine = extraction_job_input.pipeline_engine
        # check if categories passed and then append all categories to job
        pipeline_categories = []

    (
        files_data,
        valid_dataset_tags,
        valid_separate_files_uuids,
    ) = await get_all_datasets_and_files_data(
        datasets_tags=extraction_job_input.datasets,
        files_ids=extraction_job_input.files,
        current_tenant=current_tenant,
        jw_token=jw_token,
    )

    files_data = utils.delete_duplicates(files_data)

    if not (bool(files_data) ^ bool(extraction_job_input.previous_jobs)):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="No valid data (files, datasets / previous_jobs) provided",
        )

    if extraction_job_input.previous_jobs:
        previous_jobs = db_service.get_jobs_in_db_by_ids(
            db, extraction_job_input.previous_jobs
        )
        if not previous_jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Jobs with these ids do not exist.",
            )
        extraction_job_input.previous_jobs = [j.id for j in previous_jobs]

    job_name = extraction_job_input.name
    if extraction_job_input.is_draft:
        initial_status = schemas.Status.draft
    else:
        initial_status = schemas.Status.pending
    job_in_db = db_service.create_extraction_job(
        db,
        job_name,
        pipeline_id,
        pipeline_engine,
        valid_separate_files_uuids,
        valid_dataset_tags,
        files_data,
        extraction_job_input.previous_jobs,
        initial_status,
        pipeline_categories,
    )

    return job_in_db


async def create_annotation_job(
    annotation_job_input: schemas.AnnotationJobParams,
    db: Session = Depends(db_service.get_session),
) -> dbm.CombinedJob:
    """Creates new AnnotationJob and saves it in the database"""

    initial_status = (
        schemas.Status.draft
        if annotation_job_input.is_draft
        else schemas.Status.pending
    )

    created_job = db_service.create_annotation_job(
        db, annotation_job_input, initial_status
    )

    return created_job


async def create_extraction_annotation_job(
    extraction_annotation_job_input: schemas.ExtractionWithAnnotationJobParams,
    current_tenant: str,
    jw_token: str,
    db: Session = Depends(db_service.get_session),
) -> dbm.CombinedJob:
    """Creates new ExtractionWithAnnotationJob and saves it in the database"""
    if False:
        pipeline_instance = await utils.get_pipeline_instance_by_its_name(
            pipeline_name=extraction_annotation_job_input.pipeline_name,
            current_tenant=current_tenant,
            jw_token=jw_token,
            pipeline_version=extraction_annotation_job_input.pipeline_version,
        )
        pipeline_id = (
            extraction_annotation_job_input.pipeline_name
            if extraction_annotation_job_input.pipeline_name.endswith(
                ":airflow"
            )
            else pipeline_instance.get("id")
        )
        pipeline_categories = pipeline_instance.get("meta", {}).get(
            "categories", []
        )
    else:
        pipeline_id = extraction_annotation_job_input.pipeline_id
        pipeline_engine = extraction_annotation_job_input.pipeline_engine
        # check if categories passed and then append all categories to job
        pipeline_categories = []

    (
        files_data,
        valid_dataset_tags,
        valid_separate_files_uuids,
    ) = await get_all_datasets_and_files_data(
        datasets_tags=extraction_annotation_job_input.datasets,
        files_ids=extraction_annotation_job_input.files,
        current_tenant=current_tenant,
        jw_token=jw_token,
    )

    files_data = utils.delete_duplicates(files_data)
    if not (bool(files_data) ^ bool(extraction_job_input.previous_jobs)):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="No valid data (files, datasets / previous_jobs) provided",
        )

    if extraction_job_input.previous_jobs:
        previous_jobs = db_service.get_jobs_in_db_by_ids(
            db, extraction_job_input.previous_jobs
        )
        if not previous_jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Jobs with these ids do not exist.",
            )
        extraction_job_input.previous_jobs = [j.id for j in previous_jobs]

    manual_categories = extraction_annotation_job_input.categories
    categories = list(
        set(
            itertools.chain.from_iterable(
                (pipeline_categories, manual_categories or [])
            )
        )
    )

    job_in_db = db_service.create_extraction_annotation_job(
        db,
        extraction_annotation_job_input,
        pipeline_id,
        pipeline_engine,
        valid_separate_files_uuids,
        valid_dataset_tags,
        extraction_annotation_job_input.previous_jobs,
        files_data,
        categories,
    )
    return job_in_db
