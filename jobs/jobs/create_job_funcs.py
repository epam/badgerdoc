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


async def create_extraction_job(
    extraction_job_input: ExtractionJobParams,
    current_tenant: str,
    jw_token: str,
    db: Session = Depends(db_service.get_session),
) -> dbm.CombinedJob:
    """Creates new ExtractionJob and saves it in the database"""

    pipeline_instance = await utils.get_pipeline_instance_by_its_name(
        pipeline_name=extraction_job_input.pipeline_name,
        current_tenant=current_tenant,
        jw_token=jw_token,
        pipeline_version=extraction_job_input.pipeline_version,
    )

    pipeline_id = pipeline_instance.get("id")
    pipeline_categories = pipeline_instance.get("meta", {}).get("categories", [])

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

    if not files_data:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="No valid data (files, datasets) provided",
        )

    job_name = extraction_job_input.name
    if extraction_job_input.is_draft:
        initial_status = schemas.Status.draft
    else:
        initial_status = schemas.Status.pending
    job_in_db = db_service.create_extraction_job(
        db,
        job_name,
        pipeline_id,
        valid_separate_files_uuids,
        valid_dataset_tags,
        files_data,
        initial_status,
        pipeline_categories,
    )

    return job_in_db


def create_annotation_job(
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
    pipeline_instance = await utils.get_pipeline_instance_by_its_name(
        pipeline_name=extraction_annotation_job_input.pipeline_name,
        current_tenant=current_tenant,
        jw_token=jw_token,
        pipeline_version=extraction_annotation_job_input.pipeline_version,
    )
    pipeline_id = pipeline_instance.get("id")

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
    if not files_data:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="No valid data (files, datasets) provided",
        )

    pipeline_categories = pipeline_instance.get("meta", {}).get("categories", [])
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
        valid_separate_files_uuids,
        valid_dataset_tags,
        files_data,
        categories,
    )
    return job_in_db
