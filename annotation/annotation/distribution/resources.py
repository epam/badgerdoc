from typing import List

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy import and_
from sqlalchemy.orm import Session
from tenant_dependency import TenantData

from annotation.database import get_db
from annotation.distribution import (distribute, find_unassigned_files,
                                     prepare_response)
from annotation.errors import FieldConstraintError
from annotation.jobs import (check_annotators, check_validators,
                             get_job_attributes_for_post)
from annotation.microservice_communication.assets_communication import (
    get_files_info, prepare_files_for_distribution)
from annotation.microservice_communication.search import \
    X_CURRENT_TENANT_HEADER
from annotation.models import File, Job, User
from annotation.schemas import (BadRequestErrorSchema, ConnectionErrorSchema,
                                ManualAnnotationTaskSchema, TaskInfoSchema)
from annotation.tags import TASKS_TAG
from annotation.token_dependency import TOKEN

router = APIRouter(
    prefix="/distribution",
    tags=[TASKS_TAG],
    responses={500: {"model": ConnectionErrorSchema}},
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=List[ManualAnnotationTaskSchema],
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Save manual annotation tasks distribution. "
    "Distribution between users is automatic.",
)
def post_tasks(
    task_info: TaskInfoSchema,
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
):
    job_id = task_info.job_id
    job_attributes = Job.validation_type, Job.deadline
    validation_type, deadline = get_job_attributes_for_post(
        db, job_id, x_current_tenant, job_attributes
    )
    files = get_files_info(
        task_info.files, task_info.datasets, x_current_tenant, token.token
    )

    task_file_ids = {task_file["file_id"] for task_file in files}
    job_files = [
        file_db[0]
        for file_db in db.query(File.file_id)
        .filter(File.job_id == job_id)
        .all()
    ]
    files_beyond_job = task_file_ids.difference(job_files)
    if files_beyond_job:
        raise FieldConstraintError(
            f"Files with ids {files_beyond_job} are not assigned to "
            f"job {job_id}"
        )
    annotators = (
        db.query(User)
        .filter(
            and_(
                User.user_id.in_(task_info.user_ids),
                User.job_annotators.any(job_id=job_id),
            )
        )
        .all()
    )
    annotator_ids = {user.user_id for user in annotators}
    validators = (
        db.query(User)
        .filter(
            and_(
                User.user_id.in_(task_info.user_ids),
                User.job_validators.any(job_id=job_id),
            )
        )
        .all()
    )
    validator_ids = {user.user_id for user in validators}
    users_beyond_job = task_info.user_ids.difference(
        annotator_ids.union(validator_ids)
    )
    if users_beyond_job:
        raise FieldConstraintError(
            f"Users with ids {users_beyond_job} are not assigned to "
            f"job {job_id} as annotators or validators"
        )
    check_annotators(annotator_ids, validation_type)
    check_validators(validator_ids, validation_type)
    tasks = [
        task
        for task in distribute(
            db,
            files,
            annotators,
            validators,
            job_id,
            validation_type,
            deadline=(task_info.deadline or deadline),
        )
    ]
    db.commit()

    return tasks


@router.post(
    "/{job_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=List[ManualAnnotationTaskSchema],
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Distribute all remaining unassigned "
    "files and pages for given job_id.",
)
def post_tasks_for_unassigned_files(
    job_id: int = Path(..., example=3),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
):
    job = get_job_attributes_for_post(db, job_id, x_current_tenant, (Job,))

    (
        annotation_files_to_distribute,
        validation_files_to_distribute,
    ) = find_unassigned_files(job.files)
    if (
        not annotation_files_to_distribute
        and not validation_files_to_distribute
    ):
        return []
    annotation_files_to_distribute = prepare_files_for_distribution(
        annotation_files_to_distribute
    )
    validation_files_to_distribute = prepare_files_for_distribution(
        validation_files_to_distribute
    )

    response = prepare_response(
        deadline=job.deadline,
        annotation_files_to_distribute=annotation_files_to_distribute,
        validation_files_to_distribute=validation_files_to_distribute,
        annotators=job.annotators,
        validators=job.validators,
        job_id=job_id,
        validation_type=job.validation_type,
        db=db,
    )
    db.commit()
    return response
