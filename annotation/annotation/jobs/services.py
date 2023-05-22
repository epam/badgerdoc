from collections import Counter, defaultdict
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

from filter_lib import Page, form_query, map_request_to_filter, paginate
from pydantic import ValidationError
from sqlalchemy import and_, desc, not_
from sqlalchemy.orm import Session, query
from sqlalchemy.orm.attributes import InstrumentedAttribute

from annotation.categories import fetch_bunch_categories_db
from annotation.categories.services import response_object_from_db
from annotation.database import Base
from annotation.errors import (
    EnumValidationError,
    FieldConstraintError,
    WrongJobError,
)
from annotation.microservice_communication.assets_communication import (
    get_files_info,
)
from annotation.microservice_communication.jobs_communication import (
    get_job_names,
)
from annotation.models import (
    Category,
    File,
    Job,
    ManualAnnotationTask,
    User,
    association_job_annotator,
    association_job_owner,
    association_job_validator,
)
from annotation.schemas import (
    CROSS_MIN_ANNOTATORS_NUMBER,
    CategoryResponseSchema,
    FileStatusEnumSchema,
    JobInfoSchema,
    JobStatusEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)


def update_inner_job_status(
    db: Session, job_id: int, status: JobStatusEnumSchema
):
    """Updates job status in db"""
    db.query(Job).filter(Job.job_id == job_id).update({"status": status})


def get_jobs_by_files(
    db: Session, file_ids: Set[int], tenant: str, token: str
) -> DefaultDict[int, List[Dict[str, Union[int, Optional[str]]]]]:
    """
    Search for jobs, where given file_ids participate.
    Make a request to db to get list of tuples
    with file_id, job_id, job status, rows are sorted in desc
    order by job_id.
    After that dict grouped by file_id will be created:
    key: file_id, value: list of dicts with job info
    For each job separate dict with info will be created,
    structure as follows:
    {
       "id": int,
       "name": str or None,
       "status": str
    }
    None in "name" field will be set if job was not found in jobs service
    :param db: SQLAlchemy session
    :param file_ids: set of file ids, for which info about jobs
    should be gathered
    :param tenant: tenant will be passed to jobs service to get their names
    :param token: auth token will be passed to jobs service to get their names
    :return: List of dicts with job info
    """
    # SELECT files.file_id AS files_file_id,
    # jobs.job_id AS jobs_job_id,
    # jobs.status AS jobs_status
    # FROM jobs JOIN files
    # ON jobs.job_id = files.job_id AND
    # files.file_id IN (file_ids) AND
    # jobs.tenant = tenant AND
    # files.tenant = tenant
    # ORDER BY jobs.job_id DESC
    file_jobs_info = (
        db.query(File.file_id, Job.job_id, Job.status)
        .join(
            File,
            and_(
                Job.files,
                File.file_id.in_(file_ids),
                Job.tenant == tenant,
                File.tenant == tenant,
            ),
        )
        .order_by(desc(Job.job_id))
        .all()
    )

    job_ids = {job_id for _, job_id, _ in file_jobs_info}
    job_names = collect_job_names(db, list(job_ids), tenant, token)

    grouped_by_file_jobs_info = defaultdict(list)
    for file_id, job_id, status in file_jobs_info:
        grouped_by_file_jobs_info[file_id].append(
            {
                "id": job_id,
                "name": job_names.get(job_id, None),
                "status": status,
            }
        )
    return grouped_by_file_jobs_info


def get_job_attributes_for_post(
    db: Session,
    job_id: int,
    tenant: str,
    attributes: Union[Tuple[Base], Tuple[InstrumentedAttribute, ...]],
) -> Union[Job, Tuple[Any]]:
    """If Job provided in attributes - returns job instance if job exists. If
    any InstrumentedAttributes of Job provided (except join fields attributes)
    - returns tuple of such attributes values for job_id if job exists.
    """
    job_attributes = (
        db.query(*attributes).filter_by(job_id=job_id, tenant=tenant).first()
    )
    if not job_attributes:
        raise FieldConstraintError(f"wrong job_id ({job_id})")
    return job_attributes


def check_annotators(
    annotators: Set[UUID], validation_type: ValidationSchema
) -> None:
    annotators_validation_mapping = {
        ValidationSchema.cross: (
            len(annotators) < CROSS_MIN_ANNOTATORS_NUMBER,
            "There must be more than one annotator provided for cross "
            "validation job tasks creation.",
        ),
        ValidationSchema.hierarchical: (
            not annotators,
            "There must be at least one annotator provided for hierarchical "
            "validation job tasks creation.",
        ),
        ValidationSchema.validation_only: (
            annotators,
            "If the validation type is validation_only, no annotators should "
            "be provided.",
        ),
    }
    condition, error_message = annotators_validation_mapping.get(
        validation_type, (None, None)
    )  # .get with (None, None) - we may add new job type with no constraints.
    if condition:
        raise FieldConstraintError(error_message)


def check_validators(
    validators: Set[UUID], validation_type: ValidationSchema
) -> None:
    validators_validation_mapping = {
        ValidationSchema.cross: (
            validators,
            "If the validation type is cross validation, "
            "no validators should be provided.",
        ),
        ValidationSchema.hierarchical: (
            not validators,
            "If the validation type is hierarchical, validators should "
            "be provided.",
        ),
        ValidationSchema.validation_only: (
            not validators,
            "If the validation type is validation_only, validators should "
            "be provided.",
        ),
    }
    condition, error_message = validators_validation_mapping.get(
        validation_type, (None, None)
    )  # .get with (None, None) - we may add new job type with no constraints.
    if condition:
        raise FieldConstraintError(error_message)


def update_jobs_users(
    db: Session,
    job: Job,
    patch_data: dict,
    is_manual: bool = True,
) -> Tuple[Set[UUID], Set[UUID], Set[UUID]]:
    new_annotators = patch_data.get("annotators", [])
    new_validators = patch_data.get("validators", [])
    new_owners = patch_data.get("owners", [])
    users_type_validator_mapping = {
        "annotators": (new_annotators, check_annotators),
        "validators": (new_validators, check_validators),
        "owners": (new_owners, None),
    }
    new_users = {*new_annotators, *new_validators, *new_owners}
    old_users = {
        *{user.user_id for user in job.annotators},
        *{user.user_id for user in job.validators},
        *{user.user_id for user in job.owners},
    }
    annotators_to_save, validators_to_save = find_saved_users(
        db, job, set(new_annotators), set(new_validators)
    )
    deleted_users = old_users.difference(
        {*new_users, *annotators_to_save, *validators_to_save}
    )
    db_users = []
    if new_users:  # one query into DB for any possible user type provided
        old_users, added_users = find_users(db, new_users)
        db.add_all(added_users)
        db_users.extend(old_users + added_users)
    if not is_manual:
        patch_data["annotators"], patch_data["validators"] = [], []
        if isinstance(new_owners, set):
            patch_data["owners"] = list(
                {user for user in db_users if user.user_id in new_owners}
            )
        return set(), set(), set()
    # with specifying custom default iterable value in 'patch_data.get()' we
    # can make one query into database and also could check if user field
    # wasn't provided in query (empty list) or explicitly provided as empty set
    # according to pydantic schema.
    for user_type, users_with_checker in users_type_validator_mapping.items():
        users, checker = users_with_checker
        if isinstance(users, set):
            if checker:
                checker(users, job.validation_type)
            patch_data[user_type] = list(
                {user for user in db_users if user.user_id in users}
            )
    return deleted_users, annotators_to_save, validators_to_save


def add_users(
    db: Session, users: List[User], users_ids: Set[UUID]
) -> List[User]:
    users_to_add = db.query(User).filter(User.user_id.in_(users_ids)).all()
    return list(set((*users, *users_to_add)))


def update_job_categories(
    db: Session,
    patch_data: dict,
    tenant: str,
) -> None:
    new_categories = patch_data.get("categories")
    if new_categories:
        new_categories = fetch_bunch_categories_db(db, new_categories, tenant)
        patch_data["categories"] = new_categories


def validate_job_extensive_coverage(
    patch_data: dict,
    job: Job,
) -> None:
    extensive_coverage = patch_data.get("extensive_coverage")
    if extensive_coverage:
        if patch_data["annotators"]:
            annotators = patch_data["annotators"]
        else:
            annotators = job.annotators
        if len(annotators) < extensive_coverage:
            raise FieldConstraintError(
                "If the validation type is extensive_coverage number of "
                "annotators should equal or less then provided "
                "extensive_coverage number."
            )


def update_job_files(
    db: Session, patch_data: dict, job_id: int, tenant: str, token: str
) -> None:
    new_files = patch_data.pop("files", set())
    new_datasets = patch_data.pop("datasets", set())
    if new_files or new_datasets:
        new_files = get_files_info(new_files, new_datasets, tenant, token)
        db.add_all(
            [
                File(
                    file_id=new_file["file_id"],
                    tenant=tenant,
                    job_id=job_id,
                    pages_number=new_file["pages_number"],
                    status=FileStatusEnumSchema.pending,
                )
                for new_file in new_files
            ]
        )
        db.query(File).filter_by(job_id=job_id).delete()


def update_user_overall_load(db: Session, user_id: UUID) -> None:
    all_user_tasks = (
        db.query(ManualAnnotationTask)
        .filter(ManualAnnotationTask.user_id == user_id)
        .all()
    )
    pages = sum(
        (
            len(task.pages)
            for task in all_user_tasks
            if task.status != TaskStatusEnumSchema.finished
        )
    )
    user = db.query(User).get(user_id)
    user.overall_load = pages
    db.add(user)


def find_users(db: Session, users_ids: Set[UUID]):
    saved_users = db.query(User).filter(User.user_id.in_(users_ids)).all()
    saved_users_ids = {user.user_id for user in saved_users}
    new_users = [
        User(user_id=user_id)
        for user_id in users_ids.difference(saved_users_ids)
    ]
    return saved_users, new_users


def get_job(db: Session, job_id: int, tenant: str) -> Job:
    job = db.query(Job).filter_by(job_id=job_id, tenant=tenant).first()
    if not job:
        raise WrongJobError(job_id)
    return job


def filter_job_categories(
    db: Session,
    filter_query: query,
    page_size: int,
    page_num: int,
) -> Page[Union[CategoryResponseSchema, str, dict]]:
    request = {
        "pagination": {
            "page_num": page_num,
            "page_size": page_size,
        },
        "filters": [],
        "sorting": [
            {
                "field": "id",
                "direction": "asc",
            }
        ],
    }
    filter_args = map_request_to_filter(request, Category.__name__)
    category_query, pagination = form_query(filter_args, filter_query)
    try:
        response = paginate(
            [response_object_from_db(category) for category in category_query],
            pagination,
        )
    except ValidationError as exc:
        raise EnumValidationError(str(exc))
    return response


def update_files(db: Session, tasks: list, job_id: int):
    """
    Extend `distributed_annotating_pages` and
    'distributed_validating_pages' fields with distributed pages.
    file_pages: key: file_id,
    value: list of two lists, first containing pages for validation,
    second - for annotation
    file_pages:
    {
        file_id: [
                    [pages for validation],
                    [pages for annotation]
                ],
        ...
    }
    """
    file_pages = defaultdict(lambda: [[], []])
    for task in tasks:
        if task["is_validation"]:
            file_pages[int(task["file_id"])][0].extend(task["pages"])
        else:
            file_pages[int(task["file_id"])][1].extend(task["pages"])
    files = (
        db.query(File)
        .filter(
            File.file_id.in_(list(file_pages)),
            File.job_id == job_id,
        )
        .with_for_update()
        .all()
    )
    for task_file in files:
        file_pages[int(task_file.file_id)][0].extend(
            task_file.distributed_validating_pages
        )

        task_file.distributed_validating_pages = sorted(
            set(file_pages[int(task_file.file_id)][0])
        )

        file_pages[int(task_file.file_id)][1].extend(
            task_file.distributed_annotating_pages
        )
        task_file.distributed_annotating_pages = sorted(
            set(file_pages[int(task_file.file_id)][1])
        )


def recalculate_file_pages(db: Session, task_file: File):
    tasks_pages = db.query(ManualAnnotationTask.pages).filter(
        ManualAnnotationTask.job_id == task_file.job_id,
        ManualAnnotationTask.file_id == task_file.file_id,
    )

    distributed_annotating_pages = tasks_pages.filter(
        not_(ManualAnnotationTask.is_validation)
    ).all()
    pages_to_annotate = set()
    for task in distributed_annotating_pages:
        pages_to_annotate.update(task[0])
    task_file.distributed_annotating_pages = sorted(pages_to_annotate)

    distributed_validating_pages = tasks_pages.filter(
        ManualAnnotationTask.is_validation
    ).all()
    pages_to_validate = set()
    for task in distributed_validating_pages:
        pages_to_validate.update(task[0])
    task_file.distributed_validating_pages = sorted(pages_to_validate)


def read_user(db: Session, user_id: UUID):
    return db.query(User).get(user_id)


def create_user(db: Session, user_id: UUID):
    user = User(user_id=user_id)
    db.add(user)
    db.commit()
    return user


def create_job(db: Session, job_info: JobInfoSchema):
    job_info = Job(**job_info.dict())
    db.add(job_info)
    db.commit()
    return job_info


def delete_redundant_users(db: Session, users_ids: Set[UUID]):
    """Finds and deletes users who are not associated with any job"""
    annotators = db.query(User).join(association_job_annotator)
    validators = db.query(User).join(association_job_validator)
    owners = db.query(User).join(association_job_owner)
    all_users = annotators.union(validators).union(owners).all()
    all_users_ids = {user.user_id for user in all_users}
    redundant_users_ids = users_ids.difference(all_users_ids)
    if redundant_users_ids:
        db.query(User).filter(User.user_id.in_(redundant_users_ids)).delete(
            synchronize_session=False
        )


def find_saved_users(
    db: Session,
    job: Job,
    new_annotators: Set[UUID],
    new_validators: Set[UUID],
) -> Tuple[Set[UUID], Set[UUID]]:
    """Finds users who will be saved in job after update
    Updates overall load for deleted users and deletes job's tasks for them"""
    deleted_annotators = {user.user_id for user in job.annotators}.difference(
        new_annotators
    )
    deleted_validators = {user.user_id for user in job.validators}.difference(
        new_validators
    )
    annotators_to_save, validators_to_save = set(), set()
    if deleted_annotators:
        annotations_to_save = delete_tasks_for_removed_users(
            db,
            deleted_annotators,
            job.job_id,
            is_validation=False,
        )
        annotators_to_save = set(task.user_id for task in annotations_to_save)
    if deleted_validators:
        validations_to_save = delete_tasks_for_removed_users(
            db,
            deleted_validators,
            job.job_id,
            is_validation=True,
        )
        validators_to_save = set(task.user_id for task in validations_to_save)
    return annotators_to_save, validators_to_save


def delete_tasks(db: Session, tasks: Set[ManualAnnotationTask]):
    """Deletes batch of given tasks"""
    users = set()
    for task in tasks:
        task_file = (
            db.query(File)
            .filter(
                File.job_id == task.job_id,
                File.file_id == task.file_id,
            )
            .with_for_update()
            .first()
        )
        users.add(task.user_id)

        db.delete(task)
        db.flush()
        if task_file:
            recalculate_file_pages(db, task_file)

    db.flush()
    for user_id in users:
        update_user_overall_load(db, user_id)


def delete_tasks_for_removed_users(
    db: Session,
    users: Set[UUID],
    job_id: int,
    is_validation: bool,
) -> Set[ManualAnnotationTask]:
    """Deletes tasks for users that have been removed
    from job's annotators or validators if tasks were not finished"""
    tasks_to_save = set()
    tasks_to_delete = set()
    for user_id in users:
        user_tasks = (
            db.query(ManualAnnotationTask)
            .filter(
                ManualAnnotationTask.job_id == job_id,
                ManualAnnotationTask.user_id == user_id,
                ManualAnnotationTask.is_validation.is_(is_validation),
            )
            .all()
        )
        for user_task in user_tasks:
            if user_task.status == TaskStatusEnumSchema.finished:
                tasks_to_save.add(user_task)
                continue

            tasks_to_delete.add(user_task)

    delete_tasks(db, tasks_to_delete)

    return tasks_to_save


def collect_job_names(
    db: Session, job_ids: List[int], tenant: str, token: str
) -> Dict[int, str]:
    """
    Searches for jobs names in db. If names are not presented there requests
    for them to jobs microservice. Returns dict of job_ids and
    its names for provided job_ids.
    """
    job_names_in_db = (
        db.query(Job.job_id, Job.name).filter(Job.job_id.in_(job_ids)).all()
    )
    jobs_names = {}
    jobs_without_names = []
    for job in job_names_in_db:
        if not job.name:
            jobs_without_names.append(job.job_id)
        jobs_names[job.job_id] = job.name
    if jobs_without_names:
        names_from_jobs = get_job_names(jobs_without_names, tenant, token)
        jobs_names.update(names_from_jobs)
        update_jobs_names(db, names_from_jobs)
    return jobs_names


def get_jobs_by_name(
    db: Session, job_names: List[str], tenant: str
) -> Dict[int, str]:
    """
    Searches for jobs in db by job names.
    """
    job_names_in_db = (
        db.query(Job.job_id, Job.name)
        .filter(
            Job.name.in_(job_names),
            Job.tenant == tenant,
        )
        .all()
    )
    return {job_id: job_name for job_id, job_name in job_names_in_db}


def update_jobs_names(db: Session, jobs_names: Dict):
    """Updates jobs names in db"""
    for key, value in jobs_names.items():
        db.query(Job).filter(Job.job_id == key).update({Job.name: value})
    db.commit()


FileInWork = List[Dict[str, Union[int, List[int]]]]
PagesInWork = Dict[str, FileInWork]


def get_pages_in_work(
    job_tasks: Set[ManualAnnotationTask],
    tasks_to_delete: Set[ManualAnnotationTask],
) -> PagesInWork:
    task_type = {
        True: "validation",
        False: "annotation",
    }
    pages_in_work = {}
    tasks_in_work = set(job_tasks) - tasks_to_delete

    for task_in_work in tasks_in_work:
        pages_in_work.setdefault(
            task_type[task_in_work.is_validation], []
        ).append(
            {
                "file_id": task_in_work.file_id,
                "pages_number": task_in_work.pages,
            }
        )

    return pages_in_work


def get_tasks_to_delete(
    job_tasks: List[ManualAnnotationTask],
) -> Set[ManualAnnotationTask]:
    started_annotation_tasks = [
        task
        for task in job_tasks
        if (
            task.status
            in {
                TaskStatusEnumSchema.in_progress,
                TaskStatusEnumSchema.finished,
            }
            and not task.is_validation
        )
    ]
    unstarted_tasks = [
        task
        for task in job_tasks
        if task.status
        in {TaskStatusEnumSchema.pending, TaskStatusEnumSchema.ready}
    ]
    annotation_tasks_to_delete = [
        task for task in unstarted_tasks if not task.is_validation
    ]

    validation_tasks_to_delete: List[ManualAnnotationTask] = []
    # select validation tasks without starting annotations
    for validation_task in (
        task for task in unstarted_tasks if task.is_validation
    ):
        if not any(
            task
            for task in started_annotation_tasks
            if (
                task.file_id == validation_task.file_id,
                task.pages == validation_task.pages,
            )
        ):
            validation_tasks_to_delete.append(validation_task)

    return set(annotation_tasks_to_delete + validation_tasks_to_delete)


Task = Dict[str, Union[int, List[int], bool]]


def remove_pages_in_work(tasks: List[Task], pages_in_work: FileInWork):
    """Sort tasks by task pages and remove already started pages from tasks.
    All operations are inplace."""
    tasks.sort(key=lambda x: x["pages"])
    pages_in_work.sort(key=lambda x: x["pages_number"])

    for pages in pages_in_work:
        pages_to_remove = set(pages["pages_number"])

        for index, task in enumerate(tasks):
            if pages["file_id"] == task["file_id"] and any(
                page in task["pages"] for page in pages_to_remove
            ):
                same_pages = pages_to_remove.intersection(set(task["pages"]))
                task["pages"] = [
                    page for page in task["pages"] if page not in same_pages
                ]
                pages_to_remove.difference_update(same_pages)

                if not task["pages"]:
                    tasks.pop(index)

                if not pages_to_remove:
                    break


def set_task_statuses(job: Job, job_new_tasks: List[ManualAnnotationTask]):
    """Set statuses for job tasks."""
    # collect all finished annotated pages
    annotated_pages = defaultdict(Counter)
    for job_task in job_new_tasks:
        if (
            not job_task.is_validation
            and job_task.status == TaskStatusEnumSchema.finished
        ):
            annotated_pages[job_task.file_id].update(Counter(job_task.pages))

    for job_task in job_new_tasks:
        if job_task.status != TaskStatusEnumSchema.pending:
            continue
        if (
            not job_task.is_validation
            or job.validation_type == ValidationSchema.validation_only
        ):
            job_task.status = TaskStatusEnumSchema.ready
            continue

        finished_pages = annotated_pages.get(job_task.file_id, Counter())

        if all(
            page in finished_pages.keys()
            and finished_pages[page] >= count * job.extensive_coverage
            for page, count in Counter(job_task.pages).items()
        ):
            # validation task has all finished annotations
            job_task.status = TaskStatusEnumSchema.ready
            for page in job_task.pages:
                if finished_pages[page] > 0:
                    finished_pages[page] -= 1

            annotated_pages[job_task.file_id] = finished_pages
