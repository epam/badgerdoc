from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set, Union
from uuid import UUID

from annotation.distribution import prepare_response
from annotation.microservice_communication.assets_communication import (
    FilesForDistribution,
)
from annotation.models import AnnotatedDoc, Job, User
from annotation.schemas import (
    AnnotationAndValidationActionsSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from fastapi import HTTPException
from sqlalchemy import and_, asc, null, or_
from sqlalchemy.orm import Session

from .services import create_tasks

UserPages = Dict[UUID, Set[int]]


def create_annotation_tasks(
    annotation_user_for_failed_pages: Optional[str],
    task_id: int,
    db: Session,
    failed: Set[int],
    file_id: int,
    job: Job,
) -> None:
    """
    Create annotation tasks depending on
    annotation_user_for_failed_pages param.
    Validation tasks are created automatically.
    Possible values:
    initial: annotation tasks will be created for user(s), who
    annotated failed pages. Validation tasks will be created and
    distributed automatically

    auto: annotation and validation tasks for failed pages
    will be created and distributed automatically

    user_id: annotation task for failed pages will be created
    for user with provided id. Validation tasks will be
    created and distributed automatically.

    None: there are no pages, that validator marked as
    failed, hence there is no user for annotation of failed
    pages.

    Annotation tasks will be created in `ready` status,
    validation tasks will be created in `pending` status
    """
    if annotation_user_for_failed_pages:
        # dict for auto distribution of annotation and (or)
        # validation tasks
        file_to_distribute = [
            {
                "file_id": file_id,
                "pages_number": len(failed),
                "unassigned_pages": list(failed),
            }
        ]
        # annotation tasks for initial user(s)
        if (
            annotation_user_for_failed_pages
            == AnnotationAndValidationActionsSchema.initial.value
        ):
            create_tasks_initial_users(
                db, file_id, job, task_id, failed, file_to_distribute
            )

        # auto distribution of annotation and validation tasks
        elif (
            annotation_user_for_failed_pages
            == AnnotationAndValidationActionsSchema.auto.value
        ):
            # create tasks for annotation with 'ready' status
            # and validation tasks with `pending` status
            prepare_response(
                deadline=job.deadline,
                annotation_files_to_distribute=file_to_distribute,
                validation_files_to_distribute=[],
                annotators=job.annotators,
                validators=job.validators,
                job_id=job.job_id,
                validation_type=job.validation_type,
                db=db,
                annotation_tasks_status=TaskStatusEnumSchema.ready,
            )

        # annotation task for specific user
        else:
            create_annotation_tasks_specific_user(
                db,
                annotation_user_for_failed_pages,
                file_id,
                job,
                failed,
                file_to_distribute,
            )


def create_tasks_initial_users(
    db: Session,
    file_id: int,
    job: Job,
    task_id: int,
    failed: Set[int],
    file_to_distribute: FilesForDistribution,
) -> None:
    """
    Create annotation tasks with 'ready' status for initial annotators.
    Create validation tasks with 'pending' status automatically.
    """
    # revisions for job_id and file_id, made by annotators
    annotators_revisions = get_annotators_revisions(db, file_id, job.job_id, task_id)
    # find annotators, who made annotation for each page
    initial_annotators = find_initial_annotators(annotators_revisions, failed)
    # create tasks for annotation with 'ready' status
    # and tasks for validation with 'pending' status
    prepare_response(
        deadline=job.deadline,
        annotation_files_to_distribute=[],
        validation_files_to_distribute=file_to_distribute,
        annotators=job.annotators,
        validators=job.validators,
        job_id=job.job_id,
        validation_type=job.validation_type,
        db=db,
        already_created_tasks=construct_tasks(
            users=initial_annotators,
            job_id=job.job_id,
            file_id=file_id,
            is_validation=False,
            deadline=job.deadline,
            status=TaskStatusEnumSchema.ready,
        ),
    )


def create_annotation_tasks_specific_user(
    db: Session,
    annotation_user_for_failed_pages: str,
    file_id: int,
    job: Job,
    failed: Set[int],
    file_to_distribute: FilesForDistribution,
) -> None:
    """
    Create annotation task with 'ready' status for specific user.
    Create validation tasks with 'pending' status automatically.
    """
    # check, that string is valid uuid
    annotation_user_for_failed_pages = check_uuid(annotation_user_for_failed_pages)
    check_user_job_action(db, annotation_user_for_failed_pages, job.job_id, False)
    # create annotation task for specific user with 'ready' status
    # and tasks for validation with 'pending' status
    prepare_response(
        deadline=job.deadline,
        annotation_files_to_distribute=[],
        validation_files_to_distribute=file_to_distribute,
        annotators=job.annotators,
        validators=job.validators,
        job_id=job.job_id,
        validation_type=job.validation_type,
        db=db,
        already_created_tasks=construct_tasks(
            users={annotation_user_for_failed_pages: failed},
            job_id=job.job_id,
            file_id=file_id,
            is_validation=False,
            deadline=job.deadline,
            status=TaskStatusEnumSchema.ready,
        ),
    )


def get_annotators_revisions(
    db: Session, file_id: int, job_id: int, task_id: int
) -> List[AnnotatedDoc]:
    """
    Find all revisions, that have given file_id, job_id
    and do not have given task_id. Revisions are sorted
    in asc order.
    """
    return (
        db.query(AnnotatedDoc)
        .filter(
            AnnotatedDoc.file_id == file_id,
            AnnotatedDoc.job_id == job_id,
            or_(
                AnnotatedDoc.task_id != task_id,
                AnnotatedDoc.task_id == null(),
            ),
            AnnotatedDoc.pipeline == null(),
        )
        .order_by(asc(AnnotatedDoc.date))
        .all()
    )


def _find_annotators_for_failed_pages(
    revisions: List[AnnotatedDoc], pages: Set[int]
) -> Dict[int, Union[UUID, None]]:
    """
    Find the last users who annotated failed pages.
    Iterate through list of revisions, sorted in asc order,
    create dict {page: user}, where each unique page
    corresponds with the last user who annotated it.
    If the last user was deleted, i.e. None, raise exception.
    """
    pages_user = {}

    for revision in revisions:
        rev_pages = set(map(int, revision.pages))  # take unique pages
        for page in rev_pages.intersection(pages):  # take only failed by val pages
            pages_user[page] = revision.user

    if None in pages_user.values():
        raise HTTPException(
            status_code=400,
            detail="It`s not possible to create "
            "an annotation task for the initial user(s)."
            "They were deleted.",
        )
    return pages_user


def find_initial_annotators(
    revisions: List[AnnotatedDoc], pages: Set[int]
) -> UserPages:
    """
    Find last users, who annotated given pages.
    Revisions are sorted in asc order.
    1) Create dict pages_user: key: page, value: user_id. For each page find
    user, that annotated it. In this dict several elements may have same
    value (user_id).
    2) Revert dict pages_user and create
    new dict user_pages: key: user, value: list of pages.
    """
    pages_user = _find_annotators_for_failed_pages(revisions, pages)
    user_pages = defaultdict(set)
    for page, user in pages_user.items():
        user_pages[user].add(page)

    return user_pages


def construct_tasks(
    users: UserPages,
    job_id: int,
    file_id: int,
    is_validation: bool,
    deadline: datetime,
    status: TaskStatusEnumSchema,
) -> List[dict]:
    return [
        {
            "file_id": file_id,
            "pages": pages,
            "job_id": job_id,
            "user_id": user,
            "is_validation": is_validation,
            "deadline": deadline,
            "status": status,
        }
        for user, pages in users.items()
    ]


def create_validation_tasks(
    validation_user_for_reannotated_pages: Optional[str],
    annotated: Set[int],
    file_id: int,
    job: Job,
    user_id: UUID,
    db: Session,
) -> None:
    """
    Create validation tasks depending on
    validation_user_for_reannotated_pages param.
    Possible values:
    not_required: validation for edited pages is not required

    auto: validation tasks for edited pages
    will be created and distributed automatically

    user_id: validation task for edited pages will be created
    for user with provided id. Note that, if validation type of job
    is not hierarchical, user cannot assign himself for validation
    of edited pages

    None: there are no pages, edited by validator. Validation tasks
    will not be created.

    Validation tasks should be created in 'ready' status because pages are
    already reannotated by validator.
    """
    if validation_user_for_reannotated_pages:

        # auto distribution of validation tasks with 'ready' status
        if (
            validation_user_for_reannotated_pages
            == AnnotationAndValidationActionsSchema.auto.value
        ):
            file_to_distribute = [
                {
                    "file_id": file_id,
                    "pages_number": len(annotated),
                    "unassigned_pages": list(annotated),
                }
            ]
            prepare_response(
                deadline=job.deadline,
                annotation_files_to_distribute=[],
                validation_files_to_distribute=file_to_distribute,
                annotators=[
                    annotator
                    for annotator in job.annotators
                    if annotator.user_id != user_id
                ],
                validators=job.validators,
                job_id=job.job_id,
                validation_type=job.validation_type,
                db=db,
                validation_tasks_status=TaskStatusEnumSchema.ready,
            )

        # user for validation is not required
        elif (
            validation_user_for_reannotated_pages
            == AnnotationAndValidationActionsSchema.not_required
        ):
            # check, that validator is owner
            check_user_job_action(db, user_id, job.job_id, True)

        # validation task for specific user
        else:
            create_validation_tasks_specific_user(
                db,
                validation_user_for_reannotated_pages,
                user_id,
                file_id,
                job,
                annotated,
            )


def create_validation_tasks_specific_user(
    db: Session,
    validation_user_for_reannotated_pages: str,
    validator_id: UUID,
    file_id: int,
    job: Job,
    annotated: Set[int],
):
    """
    Create validation tasks for edited pages for user with
    given id.

    If given id is not valid UUID there will be exception.
    If given id does not belong to job with given job_id
    there will be exception.
    If given id matches with validator id, validation tasks
    will be created only if validation type of job is
    hierarchical, otherwise there will be exception.
    """
    # check, that string is valid uuid
    validation_user_for_reannotated_pages = check_uuid(
        validation_user_for_reannotated_pages
    )

    check_user_job_action(db, validation_user_for_reannotated_pages, job.job_id, False)

    if (
        validator_id == validation_user_for_reannotated_pages
        and job.validation_type != ValidationSchema.hierarchical
    ):
        raise HTTPException(
            status_code=400,
            detail="User cannot specify himself as "
            "validator of his own annotations in job "
            "with not hierarchical validation type.",
        )
    # create validation task for specific user with 'ready' status
    create_tasks(
        db=db,
        tasks=construct_tasks(
            users={validation_user_for_reannotated_pages: annotated},
            job_id=job.job_id,
            file_id=file_id,
            is_validation=True,
            deadline=job.deadline,
            status=TaskStatusEnumSchema.ready,
        ),
        job_id=job.job_id,
    )


def check_uuid(entity_id: str) -> UUID:
    """
    Check, that given id is a valid UUID
    """
    try:
        entity_id = UUID(entity_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Bad UUID: {entity_id}",
        )
    return entity_id


def check_user_job_action(
    db: Session, user_id: UUID, job_id: int, owner_check: bool
) -> None:
    """
    This function is used to check two cases and response with
    two custom exceptions.
    First case:
        Check, that user with given user_id is owner of the job.
        This case appears, when validator does not want to create
        validation tasks for edited by him pages.
    Second case:
        Check, that user with given user_id belongs to this job.
        This case appears, when validator wants to assign task
        for specific user.
    """
    if owner_check:
        if not check_user_job_belonging(db, user_id, job_id, only_owner=True):
            raise HTTPException(
                status_code=400,
                detail="Only owner may not request " "validation of edited pages.",
            )
    else:
        if not check_user_job_belonging(db, user_id, job_id, only_owner=False):
            raise HTTPException(
                status_code=400,
                detail=f"User with id {user_id} does not belong "
                f"to job with id {job_id}",
            )


def check_user_job_belonging(
    db: Session, user_id: UUID, job_id: int, only_owner: bool
) -> bool:
    """
    Check, that given user_id is annotator, validator or owner in
    job with given job_id.
    :param only_owner: if True, then check, that given user_id
    is in job_owners relation. Otherwise check, that
    user_id is in owners, annotators, or validators relations.
    """
    filters = [
        and_(Job.owners.any(user_id=user_id), Job.job_id == job_id),
    ]
    if not only_owner:
        filters.extend(
            [
                and_(Job.annotators.any(user_id=user_id), Job.job_id == job_id),
                and_(Job.validators.any(user_id=user_id), Job.job_id == job_id),
            ]
        )
    return bool(db.query(User).filter(or_(*filters)).first())
