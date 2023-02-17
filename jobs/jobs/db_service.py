from datetime import datetime
from typing import Any, Dict, Generator, List, Union

import jobs.config as config
import jobs.models as dbm
import jobs.schemas as schemas
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

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
    pipeline_id: int,
    valid_separate_files_ids: List[int],
    valid_dataset_ids: List[int],
    all_files_data: List[Dict[str, Any]],
    status: schemas.Status,
    categories: List[str],
) -> dbm.CombinedJob:
    """Creates new ExtractionJob in the database"""
    job_row = dbm.CombinedJob(
        name=job_name,
        status=status,
        files=valid_separate_files_ids,
        datasets=valid_dataset_ids,
        all_files_data=all_files_data,
        type=schemas.JobType.ExtractionJob,
        annotators=[],
        validators=[],
        owners=[],
        pipeline_id=pipeline_id,
        creation_datetime=datetime.utcnow(),
        categories=categories,
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
    )
    db.add(job_row)
    db.commit()
    return job_row


def create_extraction_annotation_job(
    db: Session,
    extraction_annotation_job_input: schemas.ExtractionWithAnnotationJobParams,
    pipeline_id: int,
    valid_separate_files_ids: List[int],
    valid_dataset_ids: List[int],
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
        creation_datetime=datetime.utcnow(),
        type=schemas.JobType.ExtractionWithAnnotationJob,
        annotators=extraction_annotation_job_input.annotators,
        validators=extraction_annotation_job_input.validators,
        owners=extraction_annotation_job_input.owners,
        categories=categories,
        is_auto_distribution=extraction_annotation_job_input.is_auto_distribution,  # noqa: E501
        deadline=extraction_annotation_job_input.deadline,
        validation_type=extraction_annotation_job_input.validation_type,
        pipeline_id=pipeline_id,
        all_files_data=all_files_data,
        start_manual_job_automatically=extraction_annotation_job_input.start_manual_job_automatically,  # noqa: E501
        extensive_coverage=extraction_annotation_job_input.extensive_coverage,  # noqa: E501
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
    db: Session, job_id: int
) -> Union[dbm.CombinedJob, Any]:
    """Getting hold on a job in the database by its id"""
    job_needed = db.query(dbm.CombinedJob).get(job_id)
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
    new_job_params_dict = new_job_params.dict()
    for job_param_key in new_job_params_dict:
        if new_job_params_dict[job_param_key] is not None:
            setattr(job, job_param_key, new_job_params_dict[job_param_key])
    db.commit()
