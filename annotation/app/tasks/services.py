import csv
import io
from datetime import datetime
from typing import List, Optional, Set, Tuple

from fastapi import HTTPException
from filter_lib import Page, form_query, map_request_to_filter, paginate
from sqlalchemy import and_, asc
from sqlalchemy.orm import Session

from app.errors import CheckFieldError, FieldConstraintError
from app.filters import TaskFilter
from app.jobs import update_files, update_user_overall_load
from app.models import (
    AgreementScore,
    AnnotatedDoc,
    AnnotationStatistics,
    File,
    ManualAnnotationTask,
    association_job_annotator,
    association_job_validator,
)
from app.schemas import (
    AgreementScoreServiceResponse,
    AnnotationStatisticsInputSchema,
    ExportTaskStatsInput,
    ManualAnnotationTaskInSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)


def validate_task_info(
    db: Session, task_info: dict, validation_type: ValidationSchema
) -> None:
    """Validates users-type, job-type and task-type relationship constraints
    for new/updated task as well as task's file existence for task's job and
    task's pages existence for task's file.
    """
    if (
        validation_type == ValidationSchema.validation_only
        and not task_info["is_validation"]
    ):
        raise FieldConstraintError("this job is validation only.")
    validate_users_info(db, task_info, validation_type)
    validate_files_info(db, task_info)


def validate_users_info(
    db: Session, task_info: dict, validation_type: ValidationSchema
) -> None:
    """Validates users-type, job-type and task-type relationship constraints
    for new/updated task. Raises FieldConstraintError in case of any
    validation fails.
    """
    if (
        validation_type == ValidationSchema.cross
        and task_info["is_validation"]
    ):
        check_cross_annotating_pages(db, task_info)
    if task_info["is_validation"]:
        job_task_validator = (
            db.query(
                association_job_annotator
                if validation_type == ValidationSchema.cross
                else association_job_validator
            )
            .filter_by(
                user_id=task_info["user_id"], job_id=task_info["job_id"]
            )
            .first()
        )
        if not job_task_validator:
            raise FieldConstraintError(
                f"user {task_info['user_id']} is not assigned as "
                f"validator for job {task_info['job_id']}",
            )
    else:
        job_task_annotator = (
            db.query(association_job_annotator)
            .filter_by(
                user_id=task_info["user_id"], job_id=task_info["job_id"]
            )
            .first()
        )
        if not job_task_annotator:
            raise FieldConstraintError(
                f"user {task_info['user_id']} is not assigned as "
                f"annotator for job {task_info['job_id']}",
            )


def validate_files_info(db: Session, task_info: dict) -> None:
    """Validates task's file existence for task's job and task's pages
    existence for task's file. Raises FieldConstraintError in case of any
    validation fails.
    """
    job_task_file = (
        db.query(File)
        .filter_by(file_id=task_info["file_id"], job_id=task_info["job_id"])
        .first()
    )
    if not job_task_file:
        raise FieldConstraintError(
            f"file with id {task_info['file_id']} is not assigned for "
            f"job {task_info['job_id']}"
        )
    pages_beyond_file = set(task_info["pages"]).difference(
        range(1, job_task_file.pages_number + 1)
    )
    if pages_beyond_file:
        raise FieldConstraintError(
            f"pages ({pages_beyond_file}) do not belong to "
            f"file {task_info['file_id']}"
        )


def check_cross_annotating_pages(db: Session, task_info: dict):
    """For cross annotation jobs checks that new task have no similar pages in
    created annotation tasks with same user_id, file_id and job_id. Otherwise,
    raises 'FieldConstraintError'. In cases when we are updating existing task
    'task_info.get("task_id")' will return task_id int value. In that case
    this task should not be considered within annotation pages validation.
    """
    annotation_pages = {
        page
        for task_pages in (
            db.query(ManualAnnotationTask.pages)
            .filter(
                ManualAnnotationTask.user_id == task_info["user_id"],
                ManualAnnotationTask.id != task_info.get("task_id"),
                ManualAnnotationTask.file_id == task_info["file_id"],
                ManualAnnotationTask.job_id == task_info["job_id"],
                ManualAnnotationTask.is_validation.is_(False),
            )
            .all()
        )
        for page in task_pages[0]
    }
    annotating_new_pages = annotation_pages.intersection(task_info["pages"])
    if annotating_new_pages:
        raise FieldConstraintError(
            f"within cross validation job user can't validate file's "
            f"pages that are already distributed in annotation tasks for this "
            f"user: {annotating_new_pages})"
        )


def validate_user_actions(
    is_validation: bool,
    failed: Set[int],
    annotated: Set[int],
    not_processed: Set[int],
    annotation_user: bool,
    validation_user: bool,
):
    if is_validation and failed and not annotation_user:
        raise HTTPException(
            status_code=400,
            detail="Missing `annotation_user_for_failed_pages` "
            "param for failed pages.",
        )

    if is_validation and annotated and not validation_user:
        raise HTTPException(
            status_code=400,
            detail="Missing `validation_user_for_reannotated_pages` "
            "param for edited pages.",
        )

    if is_validation and not failed and annotation_user:
        raise HTTPException(
            status_code=400,
            detail="Validator did not mark any pages as failed, "
            "thus `annotation_user_for_failed_pages` param "
            "should be null.",
        )

    if is_validation and not annotated and validation_user:
        raise HTTPException(
            status_code=400,
            detail="Validator did not edit any pages, "
            "thus `validation_user_for_reannotated_pages` param "
            "should be null.",
        )

    if is_validation and not_processed:
        raise HTTPException(
            status_code=400,
            detail="Cannot finish validation task. "
            "There are not processed pages: "
            f"{not_processed}",
        )


def create_annotation_task(
    db: Session, annotation_task: ManualAnnotationTaskInSchema
):
    annotation_task = ManualAnnotationTask(**annotation_task.dict())

    db.add(annotation_task)
    db.flush()
    update_user_overall_load(db, annotation_task.user_id)

    db.commit()
    return annotation_task


def read_annotation_tasks(
    db: Session,
    search_params: dict,
    pagination_page_size: Optional[int],
    pagination_start_page: Optional[int],
    tenant: str,
):
    total_objects = (
        db.query(ManualAnnotationTask)
        .filter_by(**search_params)
        .filter(ManualAnnotationTask.jobs.has(tenant=tenant))
        .count()
    )
    annotation_tasks = (
        db.query(ManualAnnotationTask)
        .filter_by(**search_params)
        .filter(ManualAnnotationTask.jobs.has(tenant=tenant))
        .limit(pagination_page_size)
        .offset(  # type: ignore
            (pagination_start_page - 1) * pagination_page_size,
        )
        .all()
    )
    return total_objects, annotation_tasks


def filter_tasks_db(
    db: Session,
    request: TaskFilter,
    tenant: str,
) -> Page[TaskFilter]:
    filter_query = db.query(ManualAnnotationTask).filter(
        ManualAnnotationTask.jobs.has(tenant=tenant)
    )
    filter_args = map_request_to_filter(
        request.dict(), ManualAnnotationTask.__name__
    )
    task_query, pagination = form_query(filter_args, filter_query)
    return paginate(task_query.all(), pagination)


def read_annotation_task(db: Session, task_id: int, tenant: str):
    return (
        db.query(ManualAnnotationTask)
        .filter(
            and_(
                ManualAnnotationTask.id == task_id,
                ManualAnnotationTask.jobs.has(tenant=tenant),
            ),
        )
        .first()
    )


def create_tasks(db: Session, tasks: list, job_id: int):
    db.bulk_insert_mappings(ManualAnnotationTask, tasks, return_defaults=True)
    update_files(db, tasks, job_id)

    db.flush()
    user_ids = set(user["user_id"] for user in tasks)
    for user_id in user_ids:
        update_user_overall_load(db, user_id)


def update_task_status(db: Session, task: ManualAnnotationTask) -> None:
    """Updates task's status in database if job is started and task is not
    finished (task is not in 'pending' or 'finished' statuses, otherwise
    raises FieldConstraintError with appropriate message.
    """
    task_error_messages = {
        TaskStatusEnumSchema.pending: "Job is not started yet",
        TaskStatusEnumSchema.finished: "Task is already finished",
    }
    if task.status == TaskStatusEnumSchema.ready:
        task.status = TaskStatusEnumSchema.in_progress
        db.add(task)
        db.commit()
    elif task.status in [
        TaskStatusEnumSchema.pending,
        TaskStatusEnumSchema.finished,
    ]:
        raise FieldConstraintError(
            f"Cannot save annotation for task ({task.id}). "
            f"{task_error_messages[task.status]}"
        )


def get_task_revisions(
    db: Session,
    tenant: str,
    job_id: int,
    task_id: int,
    file_id: int,
    task_pages: List[int],
) -> List[AnnotatedDoc]:
    revisions = (
        db.query(AnnotatedDoc)
        .filter(
            AnnotatedDoc.task_id == task_id,
            AnnotatedDoc.tenant == tenant,
            AnnotatedDoc.job_id == job_id,
            AnnotatedDoc.file_id == file_id,
        )
        .order_by(asc(AnnotatedDoc.date))
        .all()
    )

    for revision in revisions:
        revision.pages = {
            key: value
            for key, value in revision.pages.items()
            if int(key) in task_pages
        }
        revision.failed_validation_pages = [
            page
            for page in revision.failed_validation_pages
            if page in task_pages
        ]
        revision.validated = [
            page for page in revision.validated if page in task_pages
        ]

    return [
        revision
        for revision in revisions
        if any(
            (
                revision.pages,
                revision.failed_validation_pages,
                revision.validated,
            )
        )
    ]


def get_task_info(
    db: Session, task_id: int, tenant: str
) -> ManualAnnotationTask:
    return (
        db.query(ManualAnnotationTask)
        .filter(
            and_(
                ManualAnnotationTask.id == task_id,
                ManualAnnotationTask.jobs.has(tenant=tenant),
            ),
        )
        .first()
    )


def unblock_validation_tasks(db: Session, task: ManualAnnotationTask) -> None:
    """Gets list of already annotated_pages for task's file (including provided
    task pages) - 'annotated_file_pages'. Then searches for all 'pending'
    validation tasks for this job_id and file_id for which 'task.pages' is
    subset of annotated_file_pages list and updates such tasks status from
    'pending' to 'ready'.
    """
    annotated_file_pages = (
        db.query(File.annotated_pages)
        .filter(
            and_(
                File.file_id == task.file_id,
                File.job_id == task.job_id,
            )
        )
        .first()[0]
    )
    annotated_file_pages.extend(task.pages)
    (
        db.query(ManualAnnotationTask)
        .filter(
            and_(
                ManualAnnotationTask.job_id == task.job_id,
                ManualAnnotationTask.is_validation.is_(True),
                ManualAnnotationTask.status == TaskStatusEnumSchema.pending,
                ManualAnnotationTask.file_id == task.file_id,
                ManualAnnotationTask.pages.contained_by(annotated_file_pages),
            )
        )
        .update(
            {"status": TaskStatusEnumSchema.ready}, synchronize_session=False
        )
    )


def get_task_stats_by_id(
    db: Session,
    task_id: int,
) -> Optional[AnnotationStatistics]:
    return (
        db.query(AnnotationStatistics)
        .filter(AnnotationStatistics.task_id == task_id)
        .first()
    )


def add_task_stats_record(
    db: Session,
    task_id: int,
    stats: AnnotationStatisticsInputSchema,
) -> AnnotationStatistics:
    stats_db = get_task_stats_by_id(db, task_id)

    if stats_db:
        for name, value in stats.dict().items():
            setattr(stats_db, name, value)
        stats_db.updated = datetime.now()
    else:
        if stats.event_type == "closed":
            raise CheckFieldError(
                "Attribute event_type can not start from 'close'."
            )
        stats_db = AnnotationStatistics(task_id=task_id, **stats.dict())

    db.add(stats_db)
    db.commit()
    return stats_db


def save_agreement_scores(
    db: Session, agreement_scores: List[AgreementScoreServiceResponse]
) -> None:
    objects = [AgreementScore(**score.dict()) for score in agreement_scores]
    db.bulk_save_objects(objects)
    db.commit()


def create_export_csv(
    db: Session,
    schema: ExportTaskStatsInput,
    tenant: str,
) -> Tuple[str, bytes]:
    task_ids = {
        task.id: {
            "score": getattr(task.agreement_score, "agreement_score", None),
            "annotator": getattr(task.agreement_score, "annotator_id", None),
        }
        for task in (
            db.query(ManualAnnotationTask)
            .filter(ManualAnnotationTask.user_id == schema.user_id)
            .all()
        )
    }
    if schema.date_to:
        case = and_(
            AnnotationStatistics.created >= schema.date_from,
            AnnotationStatistics.updated <= schema.date_to,
        )
    else:
        case = AnnotationStatistics.created >= schema.date_from

    annotation_stats = [
        {
            "annotator_id": task_ids[stat.task_id]["annotator"],
            "task_id": stat.task_id,
            "task_status": stat.task.status.value,
            "time_start": stat.created.strftime("%Y/%m/%d, %H:%M:%S"),
            "time_finish": (
                stat.updated.strftime("%Y/%m/%d, %H:%M:%S")
                if stat.updated
                else None
            ),
            "agreement_score": task_ids[stat.task_id]["score"],
        }
        for stat in (
            db.query(AnnotationStatistics)
            .filter(AnnotationStatistics.task_id.in_(task_ids))
            .filter(case)
            .all()
        )
    ]
    binary = io.BytesIO()
    # Prevent from closing
    binary.close = lambda: None
    with io.TextIOWrapper(binary, encoding="utf-8", newline="") as text_file:
        keys = annotation_stats[0].keys()
        dict_writer = csv.DictWriter(text_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(annotation_stats)
    # Reset cursor
    binary.seek(0)

    today = datetime.today().strftime("%Y%m%d")
    return f"annotator_stats_export_{today}.csv", binary
