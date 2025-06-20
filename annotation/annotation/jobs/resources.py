from typing import Annotated, Dict, List, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from filter_lib import Page
from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func, or_
from sqlalchemy_filters.exceptions import BadFilterFormat
from tenant_dependency import TenantData

import annotation.categories.services
from annotation import logger as app_logger
from annotation.annotations import construct_annotated_doc
from annotation.annotations.main import (
    construct_particular_rev_response,
    get_annotations_by_revision,
)
from annotation.categories import fetch_bunch_categories_db
from annotation.database import get_db
from annotation.distribution import distribute, redistribute
from annotation.errors import NoSuchRevisionsError
from annotation.filters import CategoryFilter
from annotation.microservice_communication.assets_communication import (
    get_file_path_and_bucket,
    get_files_info,
)
from annotation.microservice_communication.jobs_communication import (
    JobUpdateException,
    update_job_status,
)
from annotation.microservice_communication.search import (
    X_CURRENT_TENANT_HEADER,
)
from annotation.schemas import (
    BadRequestErrorSchema,
    CategoryResponseSchema,
    ConnectionErrorSchema,
    DocForSaveSchema,
    FileStatusEnumSchema,
    JobFilesInfoSchema,
    JobInfoSchema,
    JobPatchOutSchema,
    JobPatchSchema,
    JobProgressSchema,
    JobStatusEnumSchema,
    JobTypeEnumSchema,
    ManualAnnotationTaskSchema,
    NotFoundErrorSchema,
    TaskStatusEnumSchema,
    UnassignedFilesInfoSchema,
    ValidationSchema,
)
from annotation.tags import FILES_TAG, JOBS_TAG
from annotation.token_dependency import TOKEN

from ..models import (
    AnnotatedDoc,
    Category,
    File,
    Job,
    ManualAnnotationTask,
    User,
)
from .services import (
    add_users,
    collect_job_names,
    delete_redundant_users,
    filter_job_categories,
    find_users,
    get_job,
    get_jobs_by_files,
    update_inner_job_status,
    update_job_categories,
    update_job_files,
    update_jobs_users,
    validate_job_extensive_coverage,
)

logger = app_logger.Logger

router = APIRouter(
    prefix="/jobs",
    responses={500: {"model": ConnectionErrorSchema}},
)


@router.post(
    "/{job_id}",
    status_code=status.HTTP_201_CREATED,
    tags=[JOBS_TAG],
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Save info about job.",
)
def post_job(
    job_info: JobInfoSchema,
    job_id: int = Path(..., examples=[3]),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
    db: Session = Depends(get_db),
):
    if db.query(Job).get(job_id):
        raise HTTPException(
            status_code=400,
            detail="The job already exists.",
        )
    validation_type = job_info.validation_type
    # todo: in case of extensive_coverage validation
    #  check if there is enough annotators but some of them have default
    #  load 0. should we throw an error or distribute load for these users
    #  despite load
    saved_users, new_users = find_users(
        db,
        {*job_info.annotators, *job_info.validators, *job_info.owners},
    )
    db.add_all(new_users)
    db_users = saved_users + new_users
    annotators = [
        user for user in db_users if user.user_id in job_info.annotators
    ]
    validators = [
        user for user in db_users if user.user_id in job_info.validators
    ]
    owners = [user for user in db_users if user.user_id in job_info.owners]
    categories = fetch_bunch_categories_db(
        db, job_info.categories, x_current_tenant, root_parents=True
    )
    is_auto_distribution = job_info.is_auto_distribution
    job_type = job_info.job_type
    db.add(
        Job(
            job_id=job_id,
            name=job_info.name,
            callback_url=job_info.callback_url,
            is_auto_distribution=is_auto_distribution,
            categories=categories,
            annotators=annotators,
            validators=validators,
            owners=owners,
            validation_type=validation_type,
            deadline=job_info.deadline,
            tenant=x_current_tenant,
            status=JobStatusEnumSchema.pending,
            job_type=job_type,
            extensive_coverage=job_info.extensive_coverage,
        )
    )

    # Revision based job if any revisions are provided
    annotated_doc_revisions = get_annotations_by_revision(
        job_info.revisions, db
    )
    if len(annotated_doc_revisions) != len(job_info.revisions):
        raise NoSuchRevisionsError("Some of the revisions were not found.")

    files = []

    if job_info.previous_jobs:
        # todo: should we use previous job id or the current one?
        for previous_job_info in job_info.previous_jobs:
            tmp_files = get_files_info(
                previous_job_info.files,
                previous_job_info.datasets,
                x_current_tenant,
                token.token,
            )
            tmp_files = [
                {
                    **f,
                    "job_id": job_id,
                    "previous_job_id": previous_job_info.job_id,
                }
                for f in tmp_files
            ]
            files += tmp_files
    else:
        revision_file_ids = [rev.file_id for rev in annotated_doc_revisions]
        files += get_files_info(
            revision_file_ids or job_info.files,
            job_info.datasets,
            x_current_tenant,
            token.token,
        )
        files = [{**f, "job_id": job_id} for f in files]

    job_type = job_info.job_type
    if (
        validation_type == ValidationSchema.validation_only
        and job_type != JobTypeEnumSchema.ExtractionJob
    ):
        db.add_all(
            [
                File(
                    file_id=f["file_id"],
                    tenant=x_current_tenant,
                    # todo: should we use previous job id or the current one?
                    job_id=f["job_id"],
                    previous_job_id=f.get("previous_job_id"),
                    pages_number=f["pages_number"],
                    distributed_annotating_pages=list(
                        range(1, f["pages_number"] + 1)
                    ),
                    annotated_pages=list(range(1, f["pages_number"] + 1)),
                    status=FileStatusEnumSchema.pending,
                )
                for f in files
            ]
        )
    else:
        db.add_all(
            [
                File(
                    file_id=f["file_id"],
                    tenant=x_current_tenant,
                    # todo: should we use previous job id or the current one?
                    job_id=f["job_id"],
                    previous_job_id=f.get("previous_job_id"),
                    pages_number=f["pages_number"],
                    status=FileStatusEnumSchema.pending,
                )
                for f in files
            ]
        )
    if is_auto_distribution and job_type != JobTypeEnumSchema.ExtractionJob:
        db.flush()
        distribute(
            db,
            files,
            annotators,
            validators,
            job_id,
            validation_type,
            deadline=job_info.deadline,
            extensive_coverage=job_info.extensive_coverage,
        )
    if job_info.revisions:  # revision based job
        # for each existing revision from other jobs we copy them over
        for annotated_doc in annotated_doc_revisions:
            rev_annotation = construct_particular_rev_response(annotated_doc)
            doc = DocForSaveSchema(
                base_revision=annotated_doc.revision,
                user=annotated_doc.user,
                pipeline=annotated_doc.pipeline,
                pages=rev_annotation.pages,
                validated=rev_annotation.validated,
                failed_validation_pages=rev_annotation.failed_validation_pages,
                similar_revisions=rev_annotation.similar_revisions,
                categories=rev_annotation.categories,
                links_json=rev_annotation.links_json,
            )
            s3_file_path, s3_file_bucket = get_file_path_and_bucket(
                file_id=annotated_doc.file_id,
                tenant=x_current_tenant,
                token=token.token,
            )
            construct_annotated_doc(
                db=db,
                # assume user_id is always the same as original revision
                user_id=annotated_doc.user,
                pipeline_id=None,
                job_id=job_id,
                file_id=annotated_doc.file_id,
                doc=doc,
                tenant=x_current_tenant,
                s3_file_path=s3_file_path,
                s3_file_bucket=s3_file_bucket,
                latest_doc=None,
                task_id=None,
                is_latest=True,
            )
    db.commit()


@router.patch(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=JobPatchOutSchema,
    tags=[JOBS_TAG],
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
    },
    summary="Update job by job_id.",
)
async def update_job(
    update_query: JobPatchSchema,
    job_id: int = Path(..., examples=[1]),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
) -> JobPatchOutSchema:
    patch_data = update_query.model_dump(exclude_unset=True)
    if not patch_data:
        return JobPatchOutSchema()
    job = get_job(db, job_id, x_current_tenant)
    if not job.name:
        collect_job_names(db, [job_id], x_current_tenant, token.token)
    if "files" in patch_data or "datasets" in patch_data:
        if job.status != JobStatusEnumSchema.pending:
            raise HTTPException(
                status_code=422,
                detail="Error: files and datasets can't be updated "
                "for already started job",
            )
        update_job_files(
            db,
            patch_data,
            job_id,
            x_current_tenant,
            token.token,
        )
    manual_users = any(
        patch_data.get(user_type) for user_type in ("annotators", "validators")
    )
    is_manual = bool(job.annotators or job.validators)
    if not is_manual and manual_users:
        raise HTTPException(
            status_code=400,
            detail="There should be no annotators or validators provided "
            f"for {job.job_type}.",
        )
    job.validation_type = patch_data.get(
        "validation_type", job.validation_type
    )
    db.flush()

    deleted_users, annotators_to_save, validators_to_save = update_jobs_users(
        db,
        job,
        patch_data,
        is_manual,
    )

    update_job_categories(db, patch_data, x_current_tenant)
    validate_job_extensive_coverage(patch_data, job)
    for field, value in patch_data.items():
        setattr(job, field, value)
    db.flush()
    if deleted_users:
        delete_redundant_users(db, deleted_users)
    if job.is_auto_distribution:
        db.flush()
        await redistribute(db, token.token, x_current_tenant, job)
    # add saved tasks users who have been removed for redistribution
    job.annotators = add_users(db, job.annotators, annotators_to_save)
    job.validators = add_users(db, job.validators, validators_to_save)
    db.commit()
    return JobPatchOutSchema(
        annotators={annotator.user_id for annotator in job.annotators},
        validators={validator.user_id for validator in job.validators},
        categories={category.id for category in job.categories},
    )


@router.get(
    "/{job_id}/files",
    status_code=status.HTTP_200_OK,
    response_model=JobFilesInfoSchema,
    tags=[FILES_TAG],
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get list of files for a particular job.",
)
def get_job_files(
    job_id: int,
    page_num: Optional[int] = Query(1, gt=0),
    page_size: Optional[int] = Query(50, gt=0, le=100),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
):
    get_job(db, job_id, x_current_tenant)
    total_objects = (
        db.query(File.file_id)
        .filter(
            File.job_id == job_id,
            File.tenant == x_current_tenant,
        )
        .count()
    )
    files = (
        db.query(File.file_id, File.status)
        .filter(
            File.job_id == job_id,
            File.tenant == x_current_tenant,
        )
        .limit(page_size)
        .offset(
            (page_num - 1) * page_size,
        )
        .all()
    )
    return JobFilesInfoSchema(
        tenant=x_current_tenant,
        job_id=job_id,
        total_objects=total_objects,
        current_page=page_num,
        page_size=page_size,
        files=[{"id": f.file_id, "status": f.status} for f in files],
    )


@router.get(
    "/{job_id}/files/unassigned",
    status_code=status.HTTP_200_OK,
    response_model=UnassignedFilesInfoSchema,
    tags=[FILES_TAG],
    summary="Get list of unassigned files by job id.",
)
def get_unassigned_files(
    job_id: int,
    page_num: Optional[int] = Query(1, gt=0),
    page_size: Optional[int] = Query(50, gt=0, le=100),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
):
    get_job(db, job_id, x_current_tenant)
    job_files = db.query(
        File.file_id,
        File.pages_number,
        File.distributed_annotating_pages,
        File.distributed_validating_pages,
    ).filter(
        File.job_id == job_id,
        File.tenant == x_current_tenant,
    )

    job_undistributed_files = job_files.filter(
        or_(
            func.cardinality(File.distributed_annotating_pages)
            != File.pages_number,
            func.cardinality(File.distributed_validating_pages)
            != File.pages_number,
        ),
    )

    current_files = (
        job_undistributed_files.limit(page_size)
        .offset(
            (page_num - 1) * page_size,
        )
        .all()
    )

    unassigned_pages = {}
    for job_file in current_files:
        required_pages = set(range(1, job_file.pages_number + 1))
        pages_to_annotate = required_pages.difference(
            set(job_file.distributed_annotating_pages)
        )
        pages_to_validate = required_pages.difference(
            set(job_file.distributed_validating_pages)
        )
        unassigned_pages[job_file.file_id] = {
            "pages_to_annotate": pages_to_annotate,
            "pages_to_validate": pages_to_validate,
        }

    return UnassignedFilesInfoSchema(
        tenant=x_current_tenant,
        job_id=job_id,
        total_objects=job_undistributed_files.count(),
        current_page=page_num,
        page_size=page_size,
        unassigned_files=[
            {
                "id": file_id,
                "pages_to_annotate": pages["pages_to_annotate"],
                "pages_to_validate": pages["pages_to_validate"],
            }
            for file_id, pages in unassigned_pages.items()
        ],
    )


@router.post(
    "/{job_id}/start",
    tags=[JOBS_TAG],
    status_code=status.HTTP_200_OK,
    response_model=List[ManualAnnotationTaskSchema],
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Start job.",
)
async def start_job(
    job_id: int = Path(..., examples=[3]),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
):
    """
    Changes status of tasks associated with
    given job_id to Ready and sends a request
    to job microservice to change
    job status to In Progress.
    """
    job = get_job(db, job_id, x_current_tenant)
    annotation_tasks = (
        db.query(ManualAnnotationTask).filter_by(job_id=job_id).all()
    )
    if not annotation_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Tasks for job_id '{job_id}' were not found.",
        )
    if (
        job.validation_type == ValidationSchema.validation_only
        and not db.query(AnnotatedDoc).filter_by(job_id=job_id).first()
    ):
        raise HTTPException(
            status_code=404,
            detail=f"Annotations for job_id '{job_id}' were not found.",
        )
    (
        db.query(ManualAnnotationTask)
        .filter(
            and_(
                ManualAnnotationTask.job_id == job_id,
                (
                    ManualAnnotationTask.is_validation.is_(False)
                    if job.validation_type != ValidationSchema.validation_only
                    else ManualAnnotationTask.is_validation.is_(True)
                ),
            )
        )
        .update(
            {"status": TaskStatusEnumSchema.ready},
            synchronize_session="evaluate",
        )
    )
    try:
        await update_job_status(
            job.callback_url,
            JobStatusEnumSchema.in_progress,
            x_current_tenant,
            token.token,
        )
    except JobUpdateException as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error: connection error ({exc.exc_info})",
        )
    update_inner_job_status(db, job_id, JobStatusEnumSchema.in_progress)
    db.commit()
    return annotation_tasks


@router.get(
    "/{job_id}/users",
    status_code=status.HTTP_200_OK,
    response_model=List[Dict[str, Union[UUID, int]]],
    tags=[JOBS_TAG],
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get list of annotators ids and their overall load for job id.",
)
def get_users_for_job(
    job_id: int = Path(..., examples=[1]),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
):
    get_job(db, job_id, x_current_tenant)

    users = (
        db.query(User.user_id, User.overall_load)
        .filter(User.job_annotators.any(job_id=job_id))
        .all()
    )
    return [
        {"id": user.user_id, "overall_load": user.overall_load}
        for user in users
    ]


# Get categories for job_id, each entity requires children/parents
@router.get(
    "/{job_id}/categories",
    status_code=status.HTTP_200_OK,
    tags=[JOBS_TAG],
    response_model=Page[Union[CategoryResponseSchema, str, dict]],
    summary="Get list of categories for provided job_id",
    responses={
        404: {"model": NotFoundErrorSchema},
    },
)
def fetch_job_categories(
    page_size: Optional[
        Annotated[int, Query(50, examples=[15], ge=1, le=100)]
    ],
    page_num: Optional[Annotated[int, Query(1, examples=[1], ge=1)]],
    job_id: int = Path(..., examples=[1]),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
) -> Page[Union[CategoryResponseSchema, str, dict]]:
    """Returns list of categories for provided job_id. Supports pagination"""
    get_job(db, job_id, x_current_tenant)
    categories_query = (
        db.query(Category)
        .join(Category.jobs)
        .filter(
            and_(
                Job.job_id == job_id,
                Job.tenant == x_current_tenant,
            )
        )
    )
    return filter_job_categories(db, categories_query, page_size, page_num)


@router.post(
    "/{job_id}/categories/search",
    status_code=status.HTTP_200_OK,
    tags=[JOBS_TAG],
    response_model=Page[Union[CategoryResponseSchema, str, dict]],
    summary="Search categories for provided job_id",
    responses={
        404: {"model": NotFoundErrorSchema},
    },
)
def search_job_categories(
    request: CategoryFilter,
    job_id: int = Path(..., examples=[1]),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
) -> Page[Union[CategoryResponseSchema, str, dict]]:
    """
    Searches and returns categories data according to search request parameters
    filters for the given {job_id}. Supports pagination and ordering.
    """
    get_job(db, job_id, x_current_tenant)
    try:
        task_response = annotation.categories.services.filter_category_db(
            db,
            request,
            x_current_tenant,
            job_id,
        )
    except BadFilterFormat as error:
        logger.exception(error)
        raise HTTPException(
            status_code=400,
            detail=f"{error}",
        )
    return task_response


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    tags=[JOBS_TAG],
    summary="Get info about jobs, in which provided file ids participate",
)
def get_jobs_info_by_files(
    file_ids: Annotated[
        List[Annotated[int, Query(ge=1)]],
        Query(
            ...,
            min_length=1,
            examples=[[1, 2, 10]],
        ),
    ],
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
    token: TenantData = Depends(TOKEN),
):

    grouped_by_file_jobs_info = get_jobs_by_files(
        db, file_ids, x_current_tenant, token.token
    )

    return {
        file_id: grouped_by_file_jobs_info.get(file_id, [])
        for file_id in file_ids
    }


@router.get(
    "/{job_id}/progress",
    status_code=status.HTTP_200_OK,
    response_model=JobProgressSchema,
    tags=[JOBS_TAG],
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get amount of job's tasks in finished status "
    "and total amount of job's tasks.",
)
def get_job_progress(
    job_id: int = Path(..., examples=[1]),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
):
    get_job(db, job_id, x_current_tenant)
    finished = (
        db.query(ManualAnnotationTask)
        .filter(
            and_(
                ManualAnnotationTask.job_id == job_id,
                ManualAnnotationTask.status == "finished",
            )
        )
        .count()
    )
    total = (
        db.query(ManualAnnotationTask)
        .filter(ManualAnnotationTask.job_id == job_id)
        .count()
    )
    return JobProgressSchema(finished=finished, total=total)
