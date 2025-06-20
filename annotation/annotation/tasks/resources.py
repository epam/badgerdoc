import os
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

import dotenv
import sqlalchemy
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse
from filter_lib import Page
from sqlalchemy import and_, not_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy_filters.exceptions import BadFilterFormat
from tenant_dependency import TenantData

from annotation.annotations import accumulate_pages_info, row_to_dict
from annotation.database import get_db
from annotation.filters import TaskFilter
from annotation.jobs import (
    collect_job_names,
    delete_tasks,
    get_job,
    get_job_attributes_for_post,
    get_jobs_by_name,
    recalculate_file_pages,
    update_files,
    update_inner_job_status,
    update_user_overall_load,
)
from annotation.logger import Logger
from annotation.microservice_communication.assets_communication import (
    get_file_names_by_request,
    get_files_by_request,
)
from annotation.microservice_communication.jobs_communication import (
    JobUpdateException,
    update_job_status,
)
from annotation.microservice_communication.search import (
    X_CURRENT_TENANT_HEADER,
    expand_response,
)
from annotation.microservice_communication.user import (
    GetUserInfoAccessDenied,
    get_user_names,
)
from annotation.schemas import (
    AnnotationStatisticsInputSchema,
    AnnotationStatisticsResponseSchema,
    BadRequestErrorSchema,
    ConnectionErrorSchema,
    ExpandedManualAnnotationTaskSchema,
    ExportTaskStatsInput,
    FileStatusEnumSchema,
    JobStatusEnumSchema,
    ManualAnnotationTaskInSchema,
    ManualAnnotationTaskSchema,
    NotFoundErrorSchema,
    PagesInfoSchema,
    PreviousAndNextTasksSchema,
    TaskPatchSchema,
    TaskStatusEnumSchema,
    ValidationEndSchema,
    ValidationSchema,
)
from annotation.tags import REVISION_TAG, TASKS_TAG
from annotation.tasks.validation import (
    create_annotation_tasks,
    create_validation_tasks,
)
from annotation.token_dependency import TOKEN

from ..models import File, Job, ManualAnnotationTask
from .services import (
    add_task_stats_record,
    count_annotation_tasks,
    create_annotation_task,
    create_export_csv,
    create_validation_revisions,
    evaluate_agreement_score,
    filter_tasks_db,
    finish_validation_task,
    get_task_info,
    get_task_revisions,
    read_annotation_task,
    read_annotation_tasks,
    save_agreement_metrics,
    unblock_validation_tasks,
    validate_ids_and_names,
    validate_task_info,
    validate_user_actions,
)

dotenv.load_dotenv(dotenv.find_dotenv())
AGREEMENT_SCORE_ENABLED = os.getenv("AGREEMENT_SCORE_ENABLED", "false")

router = APIRouter(
    prefix="/tasks",
    tags=[TASKS_TAG],
    responses={500: {"model": ConnectionErrorSchema}},
)


def _prepare_expanded_tasks_response(
    db: Session,
    file_ids: List[int],
    job_ids: List[int],
    tasks: List[ManualAnnotationTask],
    tenant: str,
    token: str,
    known_file_names: Dict[int, str] = {},
    known_job_names: Dict[int, str] = {},
) -> List[ExpandedManualAnnotationTaskSchema]:
    """
    Get names of files, jobs, logins and add them to manual annotation tasks.
    """
    files_without_name = set(file_ids) - set(known_file_names.keys())
    file_names = (
        get_file_names_by_request(list(files_without_name), tenant, token)
        if files_without_name
        else {}
    )
    file_names.update(
        (file_id, file_name)
        for file_id, file_name in known_file_names.items()
        if file_id in file_ids
    )

    jobs_without_name = set(job_ids) - set(known_job_names.keys())
    job_names = (
        collect_job_names(db, list(jobs_without_name), tenant, token)
        if jobs_without_name
        else {}
    )
    job_names.update(
        (job_id, job_name)
        for job_id, job_name in known_job_names.items()
        if job_id in job_ids
    )

    user_ids = [task.user_id for task in tasks]

    try:

        user_logins = get_user_names(user_ids, tenant, token)
    except GetUserInfoAccessDenied:
        Logger.info(
            "Trying to get users logins with non-admin jwt. "
            "Getting empty dict"
        )
        user_logins = {}

    return expand_response(tasks, file_names, job_names, user_logins)


def _construct_not_found_content(entity, entity_id):
    return f"{entity} with id [{entity_id}] was not found."


@router.post(
    "/next",
    status_code=status.HTTP_200_OK,
    response_model=ExpandedManualAnnotationTaskSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get one annotation task from assigned to a user.",
)
def get_next_annotation_task(
    user: UUID = Header(
        ..., examples=["40b6b526-d6f4-45e8-8af3-d26b5a404018"]
    ),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
):
    """
    Returns one annotation task from assigned to a user. Current - if
    there is a task with the "in_progress" status, or new, if not.
    """
    current_task = (
        db.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.user_id == user,
            ManualAnnotationTask.jobs.has(tenant=x_current_tenant),
            ManualAnnotationTask.status == TaskStatusEnumSchema.in_progress,
            not_(ManualAnnotationTask.is_validation),
        )
        .first()
    )
    if current_task:
        current_task = _prepare_expanded_tasks_response(
            db,
            [current_task.file_id],
            [current_task.job_id],
            [current_task],
            x_current_tenant,
            token.token,
        )[0]
        return current_task
    new_task = (
        db.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.user_id == user,
            ManualAnnotationTask.status == TaskStatusEnumSchema.ready,
            not_(ManualAnnotationTask.is_validation),
        )
        .first()
    )
    if new_task:
        new_task.status = TaskStatusEnumSchema.in_progress
        db.commit()
        new_task = _prepare_expanded_tasks_response(
            db,
            [new_task.file_id],
            [new_task.job_id],
            [new_task],
            x_current_tenant,
            token.token,
        )[0]
        return new_task
    raise HTTPException(
        status_code=404,
        detail=f"Can't find working tasks for user {user}.",
    )


@router.get(
    "/get_previous_and_next_tasks",
    status_code=status.HTTP_200_OK,
    summary="Get one previous and one next tasks from the one passed in",
    response_model=PreviousAndNextTasksSchema,
)
def get_next_and_previous_annotation_tasks(
    user: UUID = Header(
        ..., examples=["40b6b526-d6f4-45e8-8af3-d26b5a404018"]
    ),
    task_id: int = Query(..., examples=[1], gt=0),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
):
    active_tasks_states = (
        TaskStatusEnumSchema.ready,
        TaskStatusEnumSchema.in_progress,
    )

    previous_task_query = (
        db.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.user_id == user,
            ManualAnnotationTask.jobs.has(tenant=x_current_tenant),
            ManualAnnotationTask.id < task_id,
            ManualAnnotationTask.status.in_(active_tasks_states),
        )
        .order_by(ManualAnnotationTask.id.desc())
        .limit(1)
    )

    next_task_query = (
        db.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.user_id == user,
            ManualAnnotationTask.jobs.has(tenant=x_current_tenant),
            ManualAnnotationTask.id > task_id,
            ManualAnnotationTask.status.in_(active_tasks_states),
        )
        .order_by(ManualAnnotationTask.id)
        .limit(1)
    )

    first_task_query = _get_first_task_query(
        db, user, x_current_tenant, active_tasks_states
    )

    last_task_query = _get_first_task_query(
        db, user, x_current_tenant, active_tasks_states, reversed=True
    )

    previous_task = _get_task(previous_task_query)
    next_task = _get_task(next_task_query)

    cycled_previous_task = previous_task
    cycled_next_task = next_task
    if previous_task and not next_task:
        cycled_next_task = _get_task(first_task_query)
    if not previous_task and next_task:
        cycled_previous_task = _get_task(last_task_query)

    return PreviousAndNextTasksSchema(
        previous_task=cycled_previous_task, next_task=cycled_next_task
    )


def _get_first_task_query(
    db: Session,
    user: UUID,
    tenant: str,
    task_states: Tuple[TaskStatusEnumSchema],
    reversed: bool = False,
) -> Query:
    order_rule = (
        ManualAnnotationTask.id
        if not reversed
        else ManualAnnotationTask.id.desc()
    )
    return (
        db.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.user_id == user,
            ManualAnnotationTask.jobs.has(tenant=tenant),
            ManualAnnotationTask.status.in_(task_states),
        )
        .order_by(order_rule)
        .limit(1)
    )


def _get_task(
    query: sqlalchemy.orm.query.Query,
) -> Optional[ManualAnnotationTask]:
    try:
        return query.first()
    except AttributeError:
        """AttributeError is raised when the previous task cannot be found"""
        return None


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ManualAnnotationTaskSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Save one manual annotation task.",
)
def post_task(
    task_info: ManualAnnotationTaskInSchema,
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
):
    job_attributes = Job.validation_type, Job.deadline
    validation_type, deadline = get_job_attributes_for_post(
        db, task_info.job_id, x_current_tenant, job_attributes
    )
    task_info_dict = task_info.dict()
    validate_task_info(db, task_info_dict, validation_type)
    task_info.deadline = task_info.deadline or deadline

    update_files(db, [row_to_dict(task_info)], task_info.job_id)

    return create_annotation_task(db, task_info)


@router.post(
    "/{task_id}/stats",
    status_code=status.HTTP_201_CREATED,
    response_model=AnnotationStatisticsResponseSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Add task stats record.",
)
def add_task_stats(
    task_id: int,
    stats: AnnotationStatisticsInputSchema,
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> AnnotationStatisticsResponseSchema:
    if not read_annotation_task(db, task_id, x_current_tenant):
        return JSONResponse(
            status_code=404,
            content={"detail": f"Task with id {task_id} not found."},
        )
    stats_db = add_task_stats_record(db, task_id, stats)
    return AnnotationStatisticsResponseSchema.from_orm(stats_db)


@router.post(
    "/export",
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Export agreement score statistics for task by user_id and date",
)
def export_stats(
    user_date_schema: ExportTaskStatsInput,
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
) -> StreamingResponse:
    file_name, csv_file_binary = create_export_csv(
        db=db,
        schema=user_date_schema,
        tenant=x_current_tenant,
        token=token.token,
    )
    media_type = "text/csv"
    headers = {"Content-Disposition": f"attachment; filename={file_name}"}
    return StreamingResponse(
        csv_file_binary,
        headers=headers,
        media_type=media_type,
    )


@router.get(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=ExpandedManualAnnotationTaskSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get manual annotation task by id.",
)
def get_task(
    task_id: int = Path(..., examples=[1]),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
):
    annotation_task = read_annotation_task(db, task_id, x_current_tenant)
    if not annotation_task:
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Task with id {0} was not found.".format(task_id)
            },
        )
    annotation_task = _prepare_expanded_tasks_response(
        db,
        [annotation_task.file_id],
        [annotation_task.job_id],
        [annotation_task],
        x_current_tenant,
        token.token,
    )[0]
    return annotation_task


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Dict[
        str, Union[int, List[ExpandedManualAnnotationTaskSchema]]
    ],
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get a list of manual annotation tasks based "
    "on search parameters.",
)
def get_tasks(
    file_id: Optional[int] = Query(None, examples=[5]),
    file_name: Optional[str] = Query(None, examples=["File 1"]),
    job_id: Optional[int] = Query(None, examples=[6]),
    job_name: Optional[str] = Query(None, examples=["Job 1"]),
    user_id: Optional[UUID] = Query(
        None, examples=["2016a913-47f2-417d-afdb-032165b9330d"]
    ),
    deadline: Optional[datetime] = Query(
        None, examples=["2021-10-19 01:01:01"]
    ),
    task_status: Optional[str] = Query(
        None, examples=[TaskStatusEnumSchema.ready]
    ),
    pagination_page_size: Optional[int] = Query(
        50, gt=0, le=100, examples=[25]
    ),
    pagination_start_page: Optional[int] = Query(1, gt=0, examples=[1]),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
):
    files_by_name = (
        get_files_by_request([file_name], x_current_tenant, token.token)
        if file_name is not None
        else {}
    )
    file_ids, files_names = validate_ids_and_names(
        file_id,
        file_name,
        files_by_name,
    )

    jobs_by_name = (
        get_jobs_by_name(db, [job_name], x_current_tenant)
        if job_name is not None
        else {}
    )
    job_ids, jobs_names = validate_ids_and_names(
        job_id, job_name, jobs_by_name
    )

    search_params = {}
    for param_name, param in zip(
        ("file_ids", "job_ids", "user_id", "deadline", "status"),
        (file_ids, job_ids, user_id, deadline, task_status),
    ):
        if param:
            search_params[param_name] = param
    try:
        total_objects, annotation_tasks = read_annotation_tasks(
            db,
            search_params,
            pagination_page_size,
            pagination_start_page,
            x_current_tenant,
        )
    except SQLAlchemyError as exc:
        return JSONResponse(
            status_code=500,
            content={"detail": "Error: connection error ({0})".format(exc)},
        )
    if not annotation_tasks:
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Tasks with parameters ({0}) weren't found.".format(
                    search_params,
                )
            },
        )

    file_ids = set()
    job_ids = set()
    for task in annotation_tasks:
        file_ids.add(task.file_id)
        job_ids.add(task.job_id)
    annotation_tasks = _prepare_expanded_tasks_response(
        db,
        list(file_ids),
        list(job_ids),
        annotation_tasks,
        x_current_tenant,
        token.token,
        files_names,
        jobs_names,
    )
    return {
        "current_page": pagination_start_page,
        "page_size": pagination_page_size,
        "total_objects": total_objects,
        "annotation_tasks": annotation_tasks,
    }


@router.post(
    "/search",
    status_code=status.HTTP_200_OK,
    response_model=Page[Any],  # type: ignore
    responses={400: {"model": BadRequestErrorSchema}},
    summary="Search tasks.",
)
def search_tasks(
    request: TaskFilter,
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
):
    """Searches and returns annotation and validation tasks data according to
    search request parameters filters. Supports pagination and ordering.
    """
    try:
        task_response, files_names, jobs_names = filter_tasks_db(
            db, request, x_current_tenant, token.token
        )
    except BadFilterFormat as error:
        raise HTTPException(
            status_code=400,
            detail=f"{error}",
        )
    if not task_response.data or (
        request.filters
        and "distinct" in [item.operator.value for item in request.filters]
    ):
        return task_response
    file_ids = set()
    job_ids = set()
    annotation_tasks = task_response.data
    for task in annotation_tasks:
        file_ids.add(task.file_id)
        job_ids.add(task.job_id)
    annotation_tasks = _prepare_expanded_tasks_response(
        db,
        list(file_ids),
        list(job_ids),
        list(annotation_tasks),
        x_current_tenant,
        token.token,
        files_names,
        jobs_names,
    )
    task_response.data = annotation_tasks
    return task_response


@router.patch(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=ManualAnnotationTaskSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
    },
    summary="Update task by id.",
)
def update_task(
    update_query: TaskPatchSchema,
    task_id: int = Path(..., examples=[5]),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
):
    """
    Takes not required fields file_id, pages, job_id,
    user_id or (and) is_validation. By task`s id
    in path, updates task with tasks file and returns updated task.
    """
    patch_data = update_query.model_dump(exclude_unset=True)
    if not patch_data:
        return (
            db.query(ManualAnnotationTask)
            .filter(ManualAnnotationTask.id == task_id)
            .first()
        )
    if patch_data.get("pages"):
        patch_data["pages"] = list(patch_data["pages"])

    try:
        task = (
            db.query(ManualAnnotationTask)
            .filter(
                and_(
                    ManualAnnotationTask.id == task_id,
                    ManualAnnotationTask.jobs.has(tenant=x_current_tenant),
                )
            )
            .first()
        )
        if not task:
            raise HTTPException(
                status_code=404,
                detail=_construct_not_found_content("Task", task_id),
            )
        if task.status != TaskStatusEnumSchema.pending:
            raise HTTPException(
                status_code=400,
                detail="Error: only tasks in 'Pending' status could "
                "be updated",
            )

        task_info_dict = row_to_dict(task)

        for key, value in patch_data.items():
            task_info_dict[key] = value

        validation_type = get_job_attributes_for_post(
            db,
            task_info_dict["job_id"],
            x_current_tenant,
            (Job.validation_type,),
        )[0]
        task_info_dict["task_id"] = task_id

        validate_task_info(db, task_info_dict, validation_type)

        old_task_job_id = task.job_id
        old_task_file_id = task.file_id
        old_task_user_id = task.user_id
        old_task_file = (
            db.query(File)
            .filter(
                File.job_id == old_task_job_id,
                File.file_id == old_task_file_id,
            )
            .with_for_update()
            .first()
        )

        for param, value in patch_data.items():
            setattr(task, param, value)
        db.add(task)
        db.flush()

        if old_task_file:
            recalculate_file_pages(db, old_task_file)
        if not (
            old_task_job_id == task.job_id and old_task_file_id == task.file_id
        ):
            update_files(db, [row_to_dict(task)], task.job_id)

        db.flush()

        user_id = patch_data.get("user_id")
        if user_id and user_id != old_task_user_id:
            update_user_overall_load(db, user_id)
        update_user_overall_load(db, old_task_user_id)

        db.commit()
        return (
            db.query(ManualAnnotationTask)
            .filter(ManualAnnotationTask.id == task_id)
            .first()
        )

    except IntegrityError as err:
        raise HTTPException(
            status_code=400,
            detail=f"{err.args[0]}",
        )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Delete task by id.",
)
def delete_task(
    task_id: int = Path(..., examples=[3]),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
):
    task = (
        db.query(ManualAnnotationTask)
        .filter(
            and_(
                ManualAnnotationTask.id == task_id,
                ManualAnnotationTask.jobs.has(tenant=x_current_tenant),
            )
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=404,
            detail=_construct_not_found_content("Task", task_id),
        )
    task_file = (
        db.query(File)
        .filter(
            File.job_id == task.job_id,
            File.file_id == task.file_id,
        )
        .with_for_update()
        .first()
    )
    db.delete(task)
    db.flush()
    if task_file:
        recalculate_file_pages(db, task_file)

    db.flush()
    update_user_overall_load(db, task.user_id)

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Delete batch of tasks.",
)
def delete_batch_tasks(
    task_ids: List[int] = Body(..., examples=[1, 3, 4]),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
):
    acceptable_statuses = [
        TaskStatusEnumSchema.pending,
        TaskStatusEnumSchema.ready,
    ]
    tasks_amount = (
        db.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.id.in_(task_ids),
            ManualAnnotationTask.jobs.has(tenant=x_current_tenant),
            ManualAnnotationTask.status.in_(acceptable_statuses),
        )
        .count()
    )
    if len(task_ids) != tasks_amount:
        raise HTTPException(
            status_code=400,
            detail="Error: task(s) from given list "
            "were not found or their status does not "
            f"match with [{TaskStatusEnumSchema.pending}] "
            f"or [{TaskStatusEnumSchema.ready}].",
        )
    tasks = (
        db.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.id.in_(task_ids),
            ManualAnnotationTask.jobs.has(tenant=x_current_tenant),
        )
        .all()
    )
    delete_tasks(db, tasks)

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{task_id}/pages_summary",
    status_code=status.HTTP_200_OK,
    response_model=PagesInfoSchema,
    tags=[REVISION_TAG],
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get arrays of pages, that have been validated, "
    "marked as failed, annotated and not processed in all saved "
    "revisions by task_id",
)
def get_pages_info(
    task_id: int,
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
):
    task = get_task_info(db, task_id, x_current_tenant)

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} wasn't found.",
        )

    revisions = get_task_revisions(
        db, x_current_tenant, task.job_id, task_id, task.file_id, task.pages
    )

    validated, failed, annotated, not_processed, *_ = accumulate_pages_info(
        task.pages, revisions, unique_status=True
    )

    return PagesInfoSchema(
        validated=validated,
        failed_validation_pages=failed,
        annotated_pages=annotated,
        not_processed=not_processed,
    )


@router.post(
    "/{task_id}/finish",
    status_code=status.HTTP_200_OK,
    response_model=ManualAnnotationTaskSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
    },
    summary="Finish task.",
)
async def finish_task(
    validation_info: Optional[ValidationEndSchema] = Body(None),
    task_id: int = Path(..., examples=[3]),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
):
    """
    Changes task status to Finished by
    given id.

    If task was for annotation, searches for validation tasks that can
    be unblocked (moved from 'pending' to 'ready' status) and updates
    their statuses.
    If task was for validation, there are several
    actions for marked as failed or edited pages.

    Parameter annotation_user_for_failed_pages can be assigned
    the following values:

    initial: annotation tasks will be created for user(s), who
    annotated failed pages in 'ready' status. Validation tasks will be
    created and distributed automatically in 'pending' status.

    auto: annotation tasks (in 'ready' status) and validation tasks
    (in 'pending' status) for failed pages will be created and distributed
    automatically.

    user_id: annotation task for failed pages will be created in 'ready'
    status for user with provided id. Validation tasks will be created
    in 'pending' status and distributed automatically. Note that, if
    validation type of job is hierarchical, validator in this job
    cannot be assigned as annotator for marked as failed pages

    Parameter validation_user_for_reannotated_pages can be assigned
    the following values:

    not_required: validation for edited pages is not required

    auto: validation tasks for edited pages
    will be created in 'ready' status and distributed automatically

    user_id: validation task for edited pages will be created
    in 'ready' status for user with provided id. Note that,
    if validation type of job
    is not hierarchical, user cannot assign himself for validation
    of edited pages

    If all tasks associated with
    job are finished, sends a request to
    job microservice to update job status to Finished.
    Saves annotated/validated pages in the file.

    If all pages of the file are annotated or validated,
    the status of the file changes accordingly.
    """
    task = (
        db.query(ManualAnnotationTask)
        .filter(
            and_(
                ManualAnnotationTask.id == task_id,
                ManualAnnotationTask.jobs.has(tenant=x_current_tenant),
            )
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id [{task_id}] was not found.",
        )
    if task.status != TaskStatusEnumSchema.in_progress:
        raise HTTPException(
            status_code=400,
            detail="To finish task, its status should be: "
            f"{TaskStatusEnumSchema.in_progress}. "
            f"Actual status of task with id [{task_id}]: "
            f"{task.status}.",
        )
    if validation_info is None:
        validation_info = ValidationEndSchema()

    # if there is user for annotation
    # param will be True, otherwise False
    annotation_user = bool(
        validation_info.annotation_user_for_failed_pages is not None
    )

    # if there is user for validation
    # param will be True, otherwise False
    validation_user = bool(
        validation_info.validation_user_for_reannotated_pages is not None
    )

    if not task.is_validation and (annotation_user or validation_user):
        raise HTTPException(
            status_code=400,
            detail="This task is for annotation. "
            "There should not be "
            "info about actions for failed or edited pages.",
        )

    # find revisions, made by user
    revisions = get_task_revisions(
        db, x_current_tenant, task.job_id, task_id, task.file_id, task.pages
    )
    # accumulate info about pages, validated/annotated by him
    validated, failed, annotated, not_processed, *_ = accumulate_pages_info(
        task.pages, revisions, unique_status=True
    )
    # if same pages were annotated and marked as failed
    # it means, that these pages are edited by validator
    # and they should be validated
    failed = failed.difference(annotated)
    # if same pages were annotated and marked as validated
    # it means, that these pages are edited by validator
    # and validated (by owner), there is no need to create
    # validation tasks for them
    annotated = annotated.difference(validated)

    validate_user_actions(
        task.is_validation,
        failed,
        annotated,
        not_processed,
        annotation_user,
        validation_user,
    )
    job = get_job(db, task.job_id, x_current_tenant)
    if task.is_validation:

        # create annotation and validation tasks for pages,
        # that validator marked as failed, unless job type
        # is validation_only
        if job.validation_type != ValidationSchema.validation_only:
            create_annotation_tasks(
                validation_info.annotation_user_for_failed_pages,
                task_id=task_id,
                db=db,
                failed=failed,
                file_id=task.file_id,
                job=job,
            )
        # Create validation tasks for pages, edited by validator.
        # As all pages for validation are already annotated by user,
        # validation tasks should be created with 'ready' status (unblocked).
        create_validation_tasks(
            validation_info.validation_user_for_reannotated_pages,
            annotated=annotated,
            file_id=task.file_id,
            job=job,
            user_id=task.user_id,
            db=db,
        )
    # If user is finishing any annotation task (considering
    # extensive_coverage number), search for validation tasks
    # that can be moved from 'pending' to 'ready' status for all users within
    # job and changes validation task's statuses respectively.
    count_pages_annotations = Counter()
    count_pages_annotations.update(task.pages)
    finished_annotation_tasks = (
        db.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.job_id == task.job_id,
            ManualAnnotationTask.file_id == task.file_id,
            ManualAnnotationTask.is_validation.is_(False),
            ManualAnnotationTask.status == TaskStatusEnumSchema.finished,
        )
        .all()
    )
    for finished_task in finished_annotation_tasks:
        count_pages_annotations.update(finished_task.pages)

    finished_pages = sorted(
        filter(
            lambda x: count_pages_annotations[x] == job.extensive_coverage,
            count_pages_annotations,
        )
    )

    task.status = TaskStatusEnumSchema.finished
    same_job_tasks_amount = (
        db.query(ManualAnnotationTask)
        .filter(ManualAnnotationTask.job_id == task.job_id)
        .count()
    )
    same_job_finished_tasks_amount = (
        db.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.job_id == task.job_id,
            ManualAnnotationTask.status == TaskStatusEnumSchema.finished,
        )
        .count()
    ) + 1  # adding one to amount, because task was not committed to db yet

    task_file = (
        db.query(File)
        .filter(
            File.job_id == task.job_id,
            File.file_id == task.file_id,
        )
        .with_for_update()
        .first()
    )
    if task_file:
        if task.is_validation:
            task_file.validated_pages = sorted(
                {
                    *task_file.validated_pages,
                    *(page for page in task.pages if page in validated),
                }
            )
            if task_file.pages_number == len(task_file.validated_pages):
                task_file.status = FileStatusEnumSchema.validated

            # TODO extensive coverage, annotators, manifest_url
            extensive_coverage = task.jobs.extensive_coverage
            if (
                extensive_coverage
                and extensive_coverage > 1
                and AGREEMENT_SCORE_ENABLED == "true"
            ):
                compared_score = evaluate_agreement_score(
                    db=db,
                    task=task,
                    tenant=x_current_tenant,
                    token=token,
                )
                save_agreement_metrics(db=db, scores=compared_score)

        else:
            task_file.annotated_pages = finished_pages
            if task_file.pages_number == len(task_file.annotated_pages):
                task_file.status = FileStatusEnumSchema.annotated

    if same_job_tasks_amount == same_job_finished_tasks_amount:
        job = db.query(Job).get(task.job_id)
        try:
            await update_job_status(
                job.callback_url,
                JobStatusEnumSchema.finished,
                x_current_tenant,
                token.token,
            )
        except JobUpdateException as exc:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error: connection error ({exc.exc_info})",
            )
        update_inner_job_status(db, task.job_id, JobStatusEnumSchema.finished)

    elif (
        job.validation_type == ValidationSchema.extensive_coverage
        and AGREEMENT_SCORE_ENABLED == "true"
    ):
        annotated_count: int = count_annotation_tasks(db=db, task=task)

        current_task = int(not task.is_validation)
        if len(finished_annotation_tasks) + current_task == annotated_count:
            # call agreement score service
            compared_score = evaluate_agreement_score(
                db=db,
                task=task,
                tenant=x_current_tenant,
                token=token,
            )
            if compared_score.agreement_score_reached:
                # update a validation task and finish a job
                finish_validation_task(db=db, task=task)
                try:
                    await update_job_status(
                        job.callback_url,
                        JobStatusEnumSchema.finished,
                        x_current_tenant,
                        token.token,
                    )
                except JobUpdateException as exc:
                    db.rollback()
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error: connection error ({exc.exc_info})",
                    )
                update_inner_job_status(
                    db, task.job_id, JobStatusEnumSchema.finished
                )
            # store metrics in db
            save_agreement_metrics(db=db, scores=compared_score)

    if not task.is_validation:
        unblocked_tasks = unblock_validation_tasks(
            db, task, annotated_file_pages=finished_pages
        )
        if (
            job.validation_type == ValidationSchema.extensive_coverage
            and unblocked_tasks
        ):
            db.flush()
            # create first validation revisions with matching annotations
            create_validation_revisions(
                db, x_current_tenant, token, job.job_id, unblocked_tasks
            )

    db.flush()
    update_user_overall_load(db, task.user_id)
    db.commit()
    return task
