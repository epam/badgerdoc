import csv
import io
import os
from datetime import datetime
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple

import dotenv
import pydantic
from fastapi import HTTPException
from filter_lib import Page, form_query, map_request_to_filter, paginate
from sqlalchemy import and_, asc, text
from sqlalchemy.orm import Session
from tenant_dependency import TenantData

from app.annotations.main import (
    construct_annotated_doc,
    find_all_revisions_pages,
    load_all_revisions_pages,
)
from app.errors import CheckFieldError, FieldConstraintError
from app.filters import TaskFilter
from app.jobs import update_files, update_user_overall_load
from app.logger import Logger
from app.microservice_communication.assets_communication import (
    get_file_path_and_bucket,
)
from app.microservice_communication.task import get_agreement_score
from app.models import (
    AgreementMetrics,
    AnnotatedDoc,
    AnnotationStatistics,
    File,
    ManualAnnotationTask,
    association_job_annotator,
    association_job_validator,
)
from app.schemas import (
    AgreementScoreComparingResult,
    AgreementScoreServiceInput,
    AgreementScoreServiceResponse,
    AnnotationStatisticsInputSchema,
    DocForSaveSchema,
    ExportTaskStatsInput,
    ManualAnnotationTaskInSchema,
    ResponseScore,
    TaskMetric,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from app.schemas.annotations import PageSchema

dotenv.load_dotenv(dotenv.find_dotenv())
AGREEMENT_SCORE_MIN_MATCH = float(os.getenv("AGREEMENT_SCORE_MIN_MATCH"))


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


def finish_validation_task(db: Session, task: ManualAnnotationTask) -> None:
    db.query(ManualAnnotationTask).filter(
        ManualAnnotationTask.job_id == task.job_id,
        ManualAnnotationTask.file_id == task.file_id,
        ManualAnnotationTask.is_validation.is_(True),
    ).with_for_update().update(
        {
            ManualAnnotationTask.status: TaskStatusEnumSchema.finished  # noqa: E501
        },
        synchronize_session="fetch",
    )
    db.commit()


def count_annotation_tasks(db: Session, task: ManualAnnotationTask) -> int:
    return (
        db.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.job_id == task.job_id,
            ManualAnnotationTask.file_id == task.file_id,
            ManualAnnotationTask.is_validation.is_(False),
        )
        .count()
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


def unblock_validation_tasks(
    db: Session,
    task: ManualAnnotationTask,
    annotated_file_pages: List[int],
) -> List[ManualAnnotationTask]:
    """Having list of all annotated pages search for all 'pending'
    validation tasks for this job_id and file_id for which 'task.pages' is
    subset of annotated_file_pages list and updates such tasks status from
    'pending' to 'ready'.
    """
    unblocked_tasks = db.query(ManualAnnotationTask).filter(
        and_(
            ManualAnnotationTask.job_id == task.job_id,
            ManualAnnotationTask.is_validation.is_(True),
            ManualAnnotationTask.status == TaskStatusEnumSchema.pending,
            ManualAnnotationTask.file_id == task.file_id,
            ManualAnnotationTask.pages.contained_by(annotated_file_pages),
        )
    )
    validation_tasks = unblocked_tasks.all()
    unblocked_tasks.update(
        {"status": TaskStatusEnumSchema.ready},
        synchronize_session=False,
    )
    return validation_tasks


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
        stats_db.updated = datetime.utcnow()
    else:
        if stats.event_type == "closed":
            raise CheckFieldError(
                "Attribute event_type can not start from closed."
            )
        stats_db = AnnotationStatistics(task_id=task_id, **stats.dict())

    db.add(stats_db)
    db.commit()
    return stats_db


def create_export_csv(
    db: Session,
    schema: ExportTaskStatsInput,
    tenant: str,
) -> Tuple[str, bytes]:
    task_ids = {
        task.id: task
        for task in (
            db.query(ManualAnnotationTask)
            .filter(ManualAnnotationTask.user_id.in_(schema.user_ids))
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
            "annotator_id": str(stat.task.user_id),
            "task_id": stat.task_id,
            "task_status": stat.task.status.value,
            "file_id": stat.task.file_id,
            "pages": stat.task.pages,
            "time_start": stat.created.isoformat(),
            "time_finish": (
                stat.updated.isoformat() if stat.updated else None
            ),
            "agreement_score": [
                {
                    "task_from": metric.task_from,
                    "task_to": metric.task_to,
                    "agreement_metric": metric.agreement_metric,
                }
                for metric in stat.task.agreement_metrics
            ],
        }
        for stat in (
            db.query(AnnotationStatistics)
            .filter(AnnotationStatistics.task_id.in_(task_ids))
            .filter(case)
            .all()
        )
    ]

    if not annotation_stats:
        raise HTTPException(
            status_code=406,
            detail="Export data not found.",
        )

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


def evaluate_agreement_score(
    db: Session,
    task: ManualAnnotationTask,
    tenant: str,
    token: TenantData,
) -> AgreementScoreComparingResult:
    tasks_intersection_pages = (
        db.query(ManualAnnotationTask)
        .filter(
            # Exclude current task for the different validation type
            ManualAnnotationTask.id != task.id,
            ManualAnnotationTask.job_id == task.job_id,
            ManualAnnotationTask.file_id == task.file_id,
            ManualAnnotationTask.is_validation == False,  # noqa E712
        )
        .filter(text(f"pages && '{set(task.pages)}'"))
        .all()
    )
    tasks_intersection_pages.append(task)

    s3_file_path, s3_file_bucket = get_file_path_and_bucket(
        task.file_id, tenant, token.token
    )
    agreement_scores_input = [
        AgreementScoreServiceInput.construct(
            annotator_id=str(task_in.user_id),
            job_id=task_in.job_id,
            task_id=task_in.id,
            s3_file_path=s3_file_path,
            s3_file_bucket=s3_file_bucket,
            s3_tokens_path=f"files/{task_in.file_id}/ocr",
            # Manifest name manifest.json, same dir for the annotations files.
            manifest_url=f"annotation/{task_in.job_id}/{task_in.file_id}",
        )
        for task_in in tasks_intersection_pages
    ]
    agreement_scores: List[
        AgreementScoreServiceResponse
    ] = get_agreement_score(
        agreement_scores_input=agreement_scores_input,
        tenant=tenant,
        token=token.token,
    )
    compared_score: AgreementScoreComparingResult = compare_agreement_scores(
        agreement_scores, AGREEMENT_SCORE_MIN_MATCH
    )
    return compared_score


class _MetricScoreTuple(NamedTuple):
    task_from: int
    task_to: int
    score: float


def get_unique_scores(
    task_id: int,
    scores: List[ResponseScore],
    unique_scores: Set[_MetricScoreTuple],
) -> None:
    for score in scores:
        el = _MetricScoreTuple(task_id, score.task_id, score.agreement_score)
        unique_scores.add(
            _MetricScoreTuple(
                min(el.task_from, el.task_to),
                max(el.task_from, el.task_to),
                el.score,
            )
        )


def compare_agreement_scores(
    agreement_score_response: List[AgreementScoreServiceResponse],
    min_match: float,
) -> AgreementScoreComparingResult:
    # firstly get unique pairs of task agreement score metrics, example:
    # (1, 2, 0.95), (2, 1, 0.95) where 1 and 2 are task ids
    # there is no need to store both of them in db since they are the same
    # so transform (1, 2, 0.95), (2, 1, 0.95) to (1, 2, 0.95)
    unique_scores: Set[_MetricScoreTuple] = set()
    for entity in agreement_score_response:
        task_from_id: int = entity.task_id
        scores: List[ResponseScore] = pydantic.parse_obj_as(
            List[ResponseScore],
            entity.agreement_score if entity.agreement_score else [],
        )
        get_unique_scores(task_from_id, scores, unique_scores)

    # check is every annotator reached min match score and return result
    agreement_reached: bool = all(
        map(lambda a: a.score >= min_match, unique_scores)
    )
    metrics: List[TaskMetric] = list(
        sorted(
            map(
                lambda a: TaskMetric(
                    task_from_id=a.task_from,
                    task_to_id=a.task_to,
                    metric_score=a.score,
                ),
                unique_scores,
            ),
            key=lambda b: (b.task_from_id, b.task_to_id),
        )
    )
    return AgreementScoreComparingResult(
        agreement_score_reached=agreement_reached, task_metrics=metrics
    )


def save_agreement_metrics(
    db: Session, scores: AgreementScoreComparingResult
) -> None:
    metrics: List[AgreementMetrics] = [
        AgreementMetrics(
            task_from=el.task_from_id,
            task_to=el.task_to_id,
            agreement_metric=el.metric_score,
        )
        for el in scores.task_metrics
    ]
    db.bulk_save_objects(metrics)
    db.commit()


def get_annotation_tasks(
    db: Session,
    job_id: int,
    file_id: int,
    pages: List[int],
) -> List[ManualAnnotationTask]:
    """
    Having list of pages search for all 'finished' annotation tasks
    for job_id and file_id.
    """
    return (
        db.query(ManualAnnotationTask)
        .filter(
            and_(
                ManualAnnotationTask.job_id == job_id,
                ManualAnnotationTask.is_validation.is_(False),
                ManualAnnotationTask.status == TaskStatusEnumSchema.finished,
                ManualAnnotationTask.file_id == file_id,
                ManualAnnotationTask.pages.contained_by(pages),
            )
        )
        .all()
    )


def load_revisions(
    db: Session,
    x_current_tenant: str,
    pages_nums: List[int],
    annotation_tasks: List[ManualAnnotationTask],
) -> Dict[int, Dict[int, Dict[str, Any]]]:
    """Load all tasks revisions by given page."""
    tasks_data = dict()
    for task_number, annotation_task in enumerate(annotation_tasks):
        task_revisions = get_task_revisions(
            db,
            x_current_tenant,
            annotation_task.job_id,
            annotation_task.id,
            annotation_task.file_id,
            pages_nums,
        )
        annotated_pages = find_all_revisions_pages(task_revisions, pages_nums)
        load_all_revisions_pages(annotated_pages, x_current_tenant)

        for page_number, annotations in annotated_pages.items():
            tasks_data.setdefault(page_number, {})[task_number] = {
                "size": (
                    annotations[0]["size"]
                    if annotations
                    else {"width": 0.0, "height": 0.0}
                ),
                "objects": [
                    {key: obj[key] for key in obj if key != "id"}
                    for revision in annotations
                    for obj in revision["objs"]
                ],
                "categories": set(
                    category
                    for revision in annotations
                    for category in revision["categories"]
                ),
            }
    return tasks_data


def find_common_values(
    db: Session,
    x_current_tenant: str,
    pages_nums: List[int],
    annotation_tasks: List[ManualAnnotationTask],
) -> Tuple[List[PageSchema], Set[str]]:
    """Find common values in annotation tasks."""
    tasks_data = load_revisions(
        db, x_current_tenant, pages_nums, annotation_tasks
    )

    common_objs_pages: List[PageSchema] = []
    obj_id: int = 0
    for page_number, tasks in tasks_data.items():
        common_objs_pages.append(
            PageSchema(
                page_num=page_number,
                size=(
                    tasks[0]["size"]
                    if tasks
                    else {"width": 0.0, "height": 0.0}
                ),
                objs=[
                    {"id": (obj_id := obj_id + 1), **obj}  # noqa F841
                    for obj in tasks[
                        min(tasks.keys(), key=lambda x: len(tasks[x]))
                    ]["objects"]
                    if all(
                        obj in task_data["objects"]
                        for task_data in tasks.values()
                    )
                ],
            ),
        )

    common_categories = (
        set.intersection(
            *(
                set.intersection(
                    *(task_data["categories"] for task_data in tasks.values())
                )
                for tasks in tasks_data.values()
            )
        )
        if tasks_data
        else set()
    )

    return common_objs_pages, common_categories


def create_validation_revisions(
    db: Session,
    x_current_tenant: str,
    token: TenantData,
    job_id: int,
    finished_task: ManualAnnotationTask,
    validation_tasks: List[ManualAnnotationTask],
) -> None:
    """
    Create first validation revisions with all matching annotations from
    annotations tasks. Change validations tasks statuses to 'in_progress'.
    """
    for validation_task in validation_tasks:
        file_id = validation_task.file_id
        pages_nums = validation_task.pages

        s3_file_path, s3_file_bucket = get_file_path_and_bucket(
            file_id, x_current_tenant, token.token
        )
        annotation_tasks = get_annotation_tasks(
            db, job_id, file_id, pages_nums
        )
        annotation_tasks.append(finished_task)
        annotated_pages, categories = find_common_values(
            db, x_current_tenant, pages_nums, annotation_tasks
        )
        if not (
            (annotated_pages and any(page.objs for page in annotated_pages))
            or categories
        ):
            continue

        doc = DocForSaveSchema(
            user=validation_task.user_id,
            pages=annotated_pages,
            validated=set(),
            failed_validation_pages=set(),
            categories=categories,
        )

        try:
            construct_annotated_doc(
                db=db,
                user_id=validation_task.user_id,
                pipeline_id=None,
                job_id=job_id,
                file_id=file_id,
                doc=doc,
                tenant=x_current_tenant,
                s3_file_path=s3_file_path,
                s3_file_bucket=s3_file_bucket,
                latest_doc=None,
                task_id=validation_task.id,
                is_latest=True,
            )
        except ValueError:
            Logger.exception("Cannot save first validation revision.")
        else:
            db.flush()
            update_task_status(db, validation_task)
