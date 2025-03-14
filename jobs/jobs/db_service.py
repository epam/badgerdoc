from datetime import datetime
from typing import Any, Dict, Generator, List, Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import jobs.config as config
import jobs.models as dbm
import jobs.schemas as schemas

engine = create_engine(config.POSTGRESQL_JOBMANAGER_DATABASE_URI)
LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, None, None]:
    """Get session generator to work with the db."""
    session = LocalSession()
    try:
        yield session
    finally:
        session.close()


def create_extraction_job(
    db: Session,
    job_name: str,
    pipeline_id: Union[int, str],
    pipeline_engine: str,
    valid_separate_files_ids: List[int],
    valid_dataset_ids: List[int],
    all_files_data: List[Dict[str, Any]],
    previous_jobs: List[int],
    status: schemas.Status,
    categories: List[str],
    revisions: List[str],
) -> dbm.CombinedJob:
    """Creates new ExtractionJob in the database"""
    job_row = dbm.CombinedJob(
        name=job_name,
        status=status,
        files=valid_separate_files_ids,
        datasets=valid_dataset_ids,
        previous_jobs=previous_jobs,
        all_files_data=all_files_data,
        type=schemas.JobType.ExtractionJob,
        annotators=[],
        validators=[],
        owners=[],
        pipeline_id=pipeline_id,
        pipeline_engine=pipeline_engine,
        creation_datetime=datetime.utcnow(),
        categories=categories,
        revisions=revisions or [],
    )
    db.add(job_row)
    db.commit()
    return job_row


def create_annotation_job(
    db: Session,
    annotation_job_input: schemas.AnnotationJobParams,
    status: schemas.Status,
) -> dbm.CombinedJob:
    """Creates new AnnotationJob in the database"""
    job_row = dbm.CombinedJob(
        name=annotation_job_input.name,
        status=status,
        files=annotation_job_input.files,
        datasets=annotation_job_input.datasets,
        previous_jobs=annotation_job_input.previous_jobs,
        type=schemas.JobType.AnnotationJob.value,
        annotators=annotation_job_input.annotators,
        validators=annotation_job_input.validators,
        owners=annotation_job_input.owners,
        categories=annotation_job_input.categories,
        is_auto_distribution=annotation_job_input.is_auto_distribution,
        creation_datetime=datetime.utcnow(),
        deadline=annotation_job_input.deadline,
        validation_type=annotation_job_input.validation_type,
        extensive_coverage=annotation_job_input.extensive_coverage,
        available_annotation_types=annotation_job_input.available_annotation_types,  # noqa: E501
        available_link_types=annotation_job_input.available_link_types,
        revisions=list(annotation_job_input.revisions),
    )
    db.add(job_row)
    db.commit()
    return job_row


def create_extraction_annotation_job(
    db: Session,
    extraction_annotation_job_input: schemas.ExtractionWithAnnotationJobParams,
    pipeline_id: Union[str, int],
    pipeline_engine: str,
    valid_separate_files_ids: List[int],
    valid_dataset_ids: List[int],
    previous_jobs: List[int],
    all_files_data: List[Dict[str, Any]],
    categories: List[str],
) -> dbm.CombinedJob:
    if extraction_annotation_job_input.is_draft:
        initial_status = schemas.Status.draft
    else:
        initial_status = schemas.Status.pending

    job_row = dbm.CombinedJob(
        name=extraction_annotation_job_input.name,
        status=initial_status,
        files=valid_separate_files_ids,
        datasets=valid_dataset_ids,
        previous_jobs=previous_jobs,
        creation_datetime=datetime.utcnow(),
        type=schemas.JobType.ExtractionWithAnnotationJob,
        annotators=extraction_annotation_job_input.annotators,
        validators=extraction_annotation_job_input.validators,
        owners=extraction_annotation_job_input.owners,
        categories=categories,
        available_annotation_types=extraction_annotation_job_input.available_annotation_types,  # noqa: E501
        available_link_types=extraction_annotation_job_input.available_link_types,  # noqa: E501
        is_auto_distribution=extraction_annotation_job_input.is_auto_distribution,  # noqa: E501
        deadline=extraction_annotation_job_input.deadline,
        validation_type=extraction_annotation_job_input.validation_type,
        pipeline_id=pipeline_id,
        pipeline_engine=pipeline_engine,
        all_files_data=all_files_data,
        start_manual_job_automatically=extraction_annotation_job_input.start_manual_job_automatically,  # noqa: E501
        extensive_coverage=extraction_annotation_job_input.extensive_coverage,  # noqa: E501
        revisions=list(extraction_annotation_job_input.revisions),
    )
    db.add(job_row)
    db.commit()
    return job_row


def create_import_job(
    db: Session, import_job_input: schemas.ImportJobParams
) -> dbm.CombinedJob:
    job_row = dbm.CombinedJob(
        name=import_job_input.name,
        type=schemas.JobType.ImportJob,
        creation_datetime=datetime.utcnow(),
        import_source=import_job_input.import_source,
        import_format=import_job_input.import_format,
    )
    db.add(job_row)
    db.commit()
    return job_row


def get_all_jobs(db: Session) -> List[Dict[str, Any]]:
    """Returns a list of all jobs in the database"""
    return [job.as_dict for job in db.query(dbm.CombinedJob)]


def get_job_in_db_by_id(
    db: Session, job_id: int, with_lock=False
) -> Union[dbm.CombinedJob, Any]:
    """Getting hold on a job in the database by its id"""
    if with_lock:
        job_needed = db.query(dbm.CombinedJob).with_for_update().get(job_id)
    else:
        job_needed = db.query(dbm.CombinedJob).get(job_id)

    previous_jobs = get_jobs_in_db_by_ids(db, job_needed.previous_jobs)
    for j in previous_jobs:
        job_needed.files.extend(j.files)
    return job_needed


def get_jobs_in_db_by_ids(
    db: Session, job_ids: List[int], with_lock=False
) -> Union[List[dbm.CombinedJob], Any]:
    """Getting hold on a job in the database by its id"""
    if with_lock:
        job_needed = (
            db.query(dbm.CombinedJob)
            .with_for_update()
            .filter(dbm.CombinedJob.id.in_(job_ids))
            .all()
        )
    else:
        job_needed = (
            db.query(dbm.CombinedJob)
            .filter(dbm.CombinedJob.id.in_(job_ids))
            .all()
        )
    return job_needed


def update_job_status(
    db: Session, job: dbm.CombinedJob, new_status: schemas.Status
) -> dbm.CombinedJob:
    """Updates status of a particular job"""

    job.status = new_status.value
    db.commit()
    return job


def update_job_mode(
    db: Session, job: dbm.CombinedJob, new_mode: schemas.JobMode
) -> dbm.CombinedJob:
    """Updates status of a particular job"""
    job.mode = new_mode
    db.commit()
    return job


def delete_job(db: Session, job: dbm.CombinedJob) -> None:
    """Deletes a particular job from the database"""
    db.delete(job)
    db.commit()


def change_job(
    db: Session,
    job: dbm.CombinedJob,
    new_job_params: schemas.JobParamsToChange,
) -> None:
    """Changes any parameter of any job in db"""
    new_job_params_dict = new_job_params.dict(exclude_unset=True)
    for job_param_key in new_job_params_dict:
        if new_job_params_dict[job_param_key] is not None:
            setattr(job, job_param_key, new_job_params_dict[job_param_key])
    db.commit()


def is_job_exists_by_name(db: Session, job_name: str) -> bool:
    """ Check if a job record exist in db with the 'job_name' """
    job_count_by_name = (db
                         .query(dbm.CombinedJob)
                         .filter(dbm.CombinedJob.name == job_name)
                         .count())
    return job_count_by_name > 0
