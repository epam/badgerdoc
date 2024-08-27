"""Automatic distribution of files between annotators.

The distribution function accepts a list of files for annotation and validation
(contains id and the number of pages of each file), lists of users (annotators
and validators) among which all files should be distributed (contains info
about user id, percentages of default workload and overall workload, which
determine how many pages will be assigned to the user) and the job_id. Users
with more default workload will get more pages, while users with more overall
workload will get fewer pages. With this workload percentages of each user
his share load is calculated. Based on the total number of pages of all files,
each annotator's individual number of pages for annotation is determined. After
annotation pages distribution validators share workload for validation is
calculated with updated workload. Pages distribution for validation strategy
depends on current job's validation type. For cross-validation: list of
validators is equal to the list of annotators. User must validate only pages
that he won't annotate in this job. For hierarchical-validation: pages for
validation will be evenly distributed among 'privileged' users, specified in
validators list for this job. The sum of the pages of all files is equal
both to the sum of the annotation pages and to the sum of the validation
pages of all users. Based on this data, the algorithm searches for all possible
options for distributing whole files between users (first with the condition
that the whole files for annotation completely cover the full required load of
annotators, then with the remaining load of annotators, which cannot be
completely covered by whole files). When there are no more options for
distributing whole files between annotators, files begin to be split between
annotators, which still have an unallocated load. The algorithm tries to
allocate the maximum number of pages of one file to one annotator. After
distributing all files to all annotators, annotation tasks are created for the
current job_id. If "SPLIT_MULTIPAGE_DOC" environmental variable is set to
"false", document is not split between different users. If parameter value is
"true", it is. Also, if the variable is set to "true", tasks creation algorithm
makes sure that each annotation and validation task won't contain more than
50 pages. If page number in file that is distributed for each annotator is
greater than 50, they will be divided for tasks respectively. After that
algorithm starts to distribute files and pages for validation between
validators using same stages (whole files firstly, separate file's pages
arrays lastly - to allocate the maximum number of pages of one file to one user
for validation), considering limitations of current validation type. If there
are some remaining pages that cannot be assigned to validator with available
pages number left (e.g. for cross-validation - only user who will annotate
this pages have available pages number left), those pages will be distributed
between other validators. After last distribution, validation tasks are created
for the current job_id.
"""

import os
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union
from uuid import UUID

import dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session

from annotation.jobs import create_user, delete_tasks, read_user
from annotation.jobs.services import (
    PagesInWork,
    Task,
    get_pages_in_work,
    get_tasks_to_delete,
    remove_pages_in_work,
    set_task_statuses,
)
from annotation.microservice_communication.assets_communication import (
    FilesForDistribution,
)
from annotation.microservice_communication.jobs_communication import (
    JobUpdateException,
    update_job_status,
)
from annotation.models import File, Job, ManualAnnotationTask, User
from annotation.schemas import (
    JobStatusEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from annotation.tasks import create_tasks as create_db_tasks

dotenv.load_dotenv(dotenv.find_dotenv())
SPLIT_MULTIPAGE_DOC = os.getenv("SPLIT_MULTIPAGE_DOC", "false") == "true"
MAX_PAGES = 50

AnnotatedFilesPages = Dict[int, List[Dict[str, Union[int, List[int]]]]]
DistributionUser = Dict[str, Union[int, float, UUID]]


def prepare_users(db: Session, users_id: Iterable[UUID]) -> List[User]:
    """Check if users exist in our database, if not, then create them."""
    users = []
    for user_id in users_id:
        annotator = read_user(db, user_id)
        if not annotator:
            annotator = create_user(db, user_id)
        users.append(annotator)
    return users


def distribute(
    db: Session,
    files: FilesForDistribution,
    annotators: List[User],
    validators: List[User],
    job_id: int,
    validation_type: ValidationSchema,
    validation_files_to_distribute: FilesForDistribution = None,
    annotation_tasks_status: TaskStatusEnumSchema = TaskStatusEnumSchema.pending,  # noqa E501
    validation_tasks_status: TaskStatusEnumSchema = TaskStatusEnumSchema.pending,  # noqa E501
    already_created_tasks: List[Task] = None,
    deadline: Optional[datetime] = None,
    extensive_coverage: int = 1,
    pages_in_work: PagesInWork = None,
) -> Iterable[Task]:
    """Main script to distribute given files between given existing annotators
    for annotation and between validators for validation (depending on job's
    validation type).
    """
    if validation_files_to_distribute:
        validation_files = deepcopy(validation_files_to_distribute)
    else:
        validation_files = deepcopy(files)
    tasks = already_created_tasks if already_created_tasks else []
    create_db_tasks(db, tasks, job_id)
    db.flush()

    annotated_files_pages = {}  # no pages distributed for annotation yet
    annotators = [
        x.__dict__ for x in annotators if x.default_load  # type: ignore
    ]
    validators = [
        x.__dict__ for x in validators if x.default_load  # type: ignore
    ]
    validators_ids = [validator["user_id"] for validator in validators]
    annotation_tasks = []
    if annotators:
        if (
            validation_type == ValidationSchema.extensive_coverage
            and extensive_coverage > 1
        ):
            annotation_tasks = distribute_tasks_extensively(
                files=files,
                users=annotators,
                validators_ids=validators_ids,
                job_id=job_id,
                is_validation=False,
                tasks_status=annotation_tasks_status,
                deadline=deadline,
                extensive_coverage=extensive_coverage,
            )
        else:
            annotation_tasks = distribute_tasks(
                annotated_files_pages,
                files,
                annotators,
                job_id,
                validators_ids=validators_ids,
                is_validation=False,
                tasks_status=annotation_tasks_status,
                deadline=deadline,
            )
        # Distribute files and pages for validation considering already
        # distributed files and pages for annotation for each annotator
        if pages_in_work:
            annotations_in_work = pages_in_work.get("annotation")
            if annotations_in_work:
                remove_pages_in_work(annotation_tasks, annotations_in_work)
        create_db_tasks(db, annotation_tasks, job_id)
        db.flush()
        tasks.extend(annotation_tasks)
        if validation_type == ValidationSchema.cross:
            annotated_files_pages = find_annotated_pages(tasks)
    job_validators = choose_validators_users(
        validation_type, annotators, validators, tasks
    )
    if job_validators:
        validation_tasks = distribute_tasks(
            annotated_files_pages,
            validation_files,
            job_validators,
            job_id,
            is_validation=True,
            tasks_status=validation_tasks_status,
            deadline=deadline,
        )
        if pages_in_work:
            validations_in_work = pages_in_work.get("validation")
            if validations_in_work:
                remove_pages_in_work(validation_tasks, validations_in_work)
        create_db_tasks(db, validation_tasks, job_id)
        db.flush()
        tasks.extend(validation_tasks)
    return tasks


def choose_validators_users(
    validation_type, annotators, validators, annotation_tasks
):
    """Returns list of validators depending on validation type for this job"""
    users = {user["user_id"]: user for user in annotators + validators}
    loaded_annotators = {task["user_id"] for task in annotation_tasks}
    annotators = {annotator["user_id"] for annotator in annotators}
    validators = {validator["user_id"] for validator in validators}
    cases = {
        ValidationSchema.cross.value: (
            annotators
            if SPLIT_MULTIPAGE_DOC
            else annotators - loaded_annotators
        ),
        ValidationSchema.hierarchical.value: (
            validators
            if SPLIT_MULTIPAGE_DOC
            else validators - loaded_annotators
        ),
        ValidationSchema.validation_only.value: (
            validators
            if SPLIT_MULTIPAGE_DOC
            else validators - loaded_annotators
        ),
        ValidationSchema.extensive_coverage.value: (
            validators
            if SPLIT_MULTIPAGE_DOC
            else validators - loaded_annotators
        ),
    }
    return [users[user_id] for user_id in cases[validation_type]]


def distribute_tasks_extensively(
    files: List[Dict[str, int]],
    users: List[DistributionUser],
    validators_ids: List[str],
    job_id: int,
    is_validation: bool,
    tasks_status: TaskStatusEnumSchema,
    extensive_coverage: int,
    deadline: Optional[datetime] = None,
) -> List[Task]:

    calculate_users_load(
        files=files,
        users=users,
        extensive_coverage=extensive_coverage,
    )
    users_seen_pages = defaultdict(lambda: defaultdict(set))
    files = sorted(files, key=lambda x: x["pages_number"])
    tasks = []
    for file in files:
        annotators = sorted(
            filter(lambda x: x["pages_number"] > 0, users),
            key=lambda x: -x["pages_number"],
        )
        if not SPLIT_MULTIPAGE_DOC:
            annotators = [
                annotator
                for annotator in annotators
                if annotator["user_id"] not in validators_ids
            ] + [
                annotator
                for annotator in annotators
                if annotator["user_id"] in validators_ids
            ]
        for _ in range(extensive_coverage):
            unassigned_pages = file.get("unassigned_pages")
            pages = (
                unassigned_pages
                if unassigned_pages
                else list(range(1, file["pages_number"] + 1))
            )
            while pages:
                if (
                    SPLIT_MULTIPAGE_DOC
                    and annotators[0]["pages_number"] >= MAX_PAGES
                ):
                    user_can_take_pages = MAX_PAGES
                else:
                    user_can_take_pages = annotators[0]["pages_number"]

                user_can_take_pages = min(len(pages), user_can_take_pages)
                pages_not_seen_by_user = sorted(
                    set(pages).difference(
                        users_seen_pages[annotators[0]["user_id"]][
                            file["file_id"]
                        ]
                    )
                )

                if not pages_not_seen_by_user:
                    annotators.pop(0)
                    continue
                if SPLIT_MULTIPAGE_DOC:
                    pages_for_user = pages_not_seen_by_user[
                        :user_can_take_pages
                    ]
                else:
                    pages_for_user = pages_not_seen_by_user
                    user_page_correction = (
                        len(pages_not_seen_by_user)
                        - annotators[0]["pages_number"]
                    )
                    if user_page_correction > 0:
                        annotators[0]["pages_number"] += user_page_correction
                        for annotator in annotators[1:]:
                            annotator["pages_number"] -= user_page_correction
                            if annotator["pages_number"] < 0:
                                user_page_correction = abs(
                                    annotator["pages_number"]
                                )
                                annotator["pages_number"] = 0
                                continue
                            break
                        annotators = [
                            annotator
                            for annotator in annotators
                            if annotator["pages_number"]
                        ]

                tasks.append(
                    {
                        "file_id": file["file_id"],
                        "pages": pages_for_user,
                        "job_id": job_id,
                        "user_id": annotators[0]["user_id"],
                        "is_validation": is_validation,
                        "status": tasks_status,
                        "deadline": deadline,
                    }
                )
                users_seen_pages[annotators[0]["user_id"]][
                    file["file_id"]
                ].update(set(pages_for_user))
                pages = sorted(set(pages).difference(set(pages_for_user)))
                annotators[0]["pages_number"] -= len(pages_for_user)
                if annotators[0]["pages_number"] == 0:
                    annotators.pop(0)
    # merge tasks for annotators if it's possible.

    ...

    return tasks


def find_annotated_pages(annotation_tasks: List[Task]) -> AnnotatedFilesPages:
    """Constructs dict with information of already distributed for annotation
    files and pages for each annotator"""
    annotated_files_pages = defaultdict(list)
    for task in annotation_tasks:
        file_info = {"file_id": task["file_id"], "pages": task["pages"]}
        annotated_files_pages[task["user_id"]].append(file_info)
    return annotated_files_pages


def distribute_tasks(
    annotated_files_pages: AnnotatedFilesPages,
    files: List[Dict[str, int]],
    users: List[DistributionUser],
    job_id: int,
    is_validation: bool,
    tasks_status: TaskStatusEnumSchema,
    deadline: Optional[datetime] = None,
    validators_ids: List[str] = [],
) -> List[Task]:
    """Distribution script. Distribution strategy depends on task type -
    annotation or validation. Create tasks with distributed whole files firstly
    and with partial files - lastly. Returns all created tasks.
    """
    calculate_users_load(files, users)  # type: ignore
    if not SPLIT_MULTIPAGE_DOC:
        users[:] = [
            user for user in users if user["user_id"] not in validators_ids
        ] + [user for user in users if user["user_id"] in validators_ids]

    tasks = distribute_whole_files(  # type: ignore
        annotated_files_pages,
        files,
        users,
        job_id,
        is_validation,
        tasks_status,
        deadline,
    )
    # distribution of partial files pages for annotation and validation has
    # different algorithm so function choice depends on distribution type
    partial_tasks = (
        distribute_validation_partial_files(
            annotated_files_pages, files, users, job_id, tasks_status, deadline
        )
        if is_validation
        else distribute_annotation_partial_files(
            files, users, job_id, tasks_status, deadline
        )  # type: ignore
    )
    tasks.extend(partial_tasks)

    return tasks


def calculate_users_load(
    files: List[Dict[str, int]],
    users: List[DistributionUser],
    extensive_coverage: int = 1,
):
    """Distribute page amount of all files between users depending on the
    default and overall load of users."""
    all_users_default_load = sum(x["default_load"] for x in users)
    all_job_pages_sum = sum(x["pages_number"] for x in files)
    pages_with_extensive_coverage = all_job_pages_sum * extensive_coverage
    average_job_pages = all_job_pages_sum / len(users)
    all_users_overall_load = sum(x["overall_load"] for x in users)
    all_users_share_load = find_users_share_loads(
        users=users,
        all_job_pages_sum=all_job_pages_sum,
        average_job_pages=average_job_pages,
        users_default_load=all_users_default_load,
        users_overall_load=all_users_overall_load,
    )

    pages_left_for_distribute = pages_with_extensive_coverage
    for user in users:
        user["share_load"] = user["share_load"] / all_users_share_load
        pages_number_for_user = min(
            round(pages_with_extensive_coverage * user["share_load"]),
            all_job_pages_sum,
        )

        pages_left_for_distribute -= pages_number_for_user
        user["pages_number"] = pages_number_for_user

    users.sort(key=lambda x: x["pages_number"], reverse=True)
    while pages_left_for_distribute > 0:
        for user in users:
            if not pages_left_for_distribute:
                break
            if user["pages_number"] < all_job_pages_sum:
                pages_number_for_user = min(
                    all_job_pages_sum - user["pages_number"],
                    max(
                        round(pages_left_for_distribute * user["share_load"]),
                        1,
                    ),
                )
                pages_left_for_distribute -= pages_number_for_user
                user["pages_number"] += pages_number_for_user

    # Correct the difference between all files pages and all users load
    # pages caused by rounding. Fix it on the most loaded user:
    users[0]["pages_number"] += pages_with_extensive_coverage - sum(
        x["pages_number"] for x in users
    )


def find_users_share_loads(
    users: List[DistributionUser],
    all_job_pages_sum: int,
    average_job_pages: float,
    users_default_load: int,
    users_overall_load: int,
) -> float:
    """Calculates each user's share load. Overall_load parts depend on average
    overall_load (pages number) for all users. If user has less overall_load
    than average overall pages load he will receive more pages in this job and
    vice versa. The more load deviation from average value user has - the
    mare/less pages he will receive. Maximum dispersion may not exceed average
    load for this job. After calculating overall part of share load algorithms
    calculates resulting share load with considering product of default and
    overall load part for user. Function modifies user["share_load"] for every
    user with result loads product and returns share load sum for all users.
    """
    quantity = len(users)
    for user in users:
        average_pages_deviation = (
            users_overall_load - user["overall_load"] * quantity
        )
        average_deviation_coefficient = (
            average_pages_deviation / (users_overall_load * quantity)
            if users_overall_load
            else 0
        )
        pages_deviation = average_deviation_coefficient * average_job_pages
        user_deviation_pages = average_job_pages + pages_deviation
        user["share_load"] = (
            user_deviation_pages / all_job_pages_sum
            if all_job_pages_sum
            else 1
        )
        default_load_part = user["default_load"] / users_default_load
        user["share_load"] *= default_load_part
    all_annotators_share_load = sum(
        annotator["share_load"] for annotator in users
    )
    return all_annotators_share_load


def distribute_whole_files(
    annotated_files_pages: AnnotatedFilesPages,
    files: List[Dict[str, int]],
    users: List[DistributionUser],
    job_id: int,
    is_validation: bool,
    tasks_status: TaskStatusEnumSchema,
    deadline: Optional[datetime] = None,
) -> List[Task]:
    """Create annotation/validation tasks from whole files. When distribute
    files for cross validation - consider only not annotated files (fully or
    partly) for each user"""
    tasks = []
    user_page_correction = 0
    for user in users:
        if not user["pages_number"]:
            continue
        if user_page_correction:
            user["pages_number"] -= user_page_correction
            if user["pages_number"] < 0:
                user_page_correction = abs(user["pages_number"])
                user["pages_number"] = 0
                continue
        annotated_files = []
        annotator_files = annotated_files_pages.get(user["user_id"])
        if annotator_files:
            annotated_files.extend(item["file_id"] for item in annotator_files)
        files_to_distribute = [
            item for item in files if item["file_id"] not in annotated_files
        ]
        files_for_task = find_equal_files(
            files_to_distribute, user["pages_number"]
        )
        create_tasks(
            tasks,
            files_for_task,
            user,
            job_id,
            is_validation,
            tasks_status,
            deadline,
        )
        files_for_task, user_page_correction = find_small_files(
            files_to_distribute, user["pages_number"]
        )
        user["pages_number"] += user_page_correction
        create_tasks(
            tasks,
            files_for_task,
            user,
            job_id,
            is_validation,
            tasks_status,
            deadline,
        )
    if user_page_correction != 0:
        for user in users:
            if user["pages_number"] > 0:
                user["pages_number"] -= user_page_correction
                if user["pages_number"] < 0:
                    user_page_correction = abs(user["pages_number"])
                    user["pages_number"] = 0
                    continue
                break
    return tasks  # type: ignore


def find_files_for_task(
    files: List[Dict[str, int]],
    pages_for_task: List[int],
) -> List[Dict[str, int]]:
    """Find files from the list of files by the required page
    numbers."""
    files_for_task = []
    distributed_files = []
    for pages in pages_for_task:
        file_for_task = next(
            x
            for x in files
            if x["pages_number"] == pages
            and x["file_id"] not in distributed_files
        )
        files_for_task.append(file_for_task)
        distributed_files.append(file_for_task["file_id"])
    return files_for_task


def find_equal_files(
    files: List[Dict[str, int]], user_pages: int
) -> List[Dict[str, int]]:
    """Find the same or combined files where the sum of the amount of pages
    equals the user load."""
    file_pages = [x["pages_number"] for x in files if x["pages_number"]]
    pages_for_task = get_page_number_combinations(file_pages, user_pages)
    return find_files_for_task(files, pages_for_task)


def get_page_number_combinations(
    file_pages: List[int],
    user_pages: int,
) -> List[int]:
    """Find the same or combined number of pages which sum is equal
    to the user load (in page numbers)"""
    stack, combination_result = [(file_pages, [], 0)], []
    while stack:
        remaining, combinations, combinations_sum = stack.pop()
        if combinations_sum == user_pages:
            combination_result.extend(combinations)
            break
        if combinations_sum > user_pages or not remaining:
            continue

        file_page = remaining[0]
        remaining = remaining[1:]
        stack.append((remaining, combinations, combinations_sum))
        stack.append(
            (
                remaining,
                combinations + [file_page],
                combinations_sum + file_page,
            )
        )
    return combination_result


def create_tasks(
    tasks: List[Task],
    files_for_task: List[Dict[str, int]],
    user: DistributionUser,
    job_id: int,
    is_validation: bool,
    status: TaskStatusEnumSchema,
    deadline: Optional[datetime] = None,
) -> None:
    """Prepare annotation/validation tasks and decrease annotator and files
    pages numbers. If "SPLIT_MULTIPAGE_DOC" environmental variable is set to
    "true", each task doesn't contain more than 50 pages. If page number
    in file for distribution is greater than 50, they will be divided in
    different tasks respectively.
    """
    for file_for_task in files_for_task:
        # field unassigned_pages contains specific unassigned pages in file
        # if this field is not present, all pages if file are unassigned
        pages = file_for_task.get(
            "unassigned_pages",
            list(range(1, file_for_task["pages_number"] + 1)),
        )
        full_tasks = len(pages) // MAX_PAGES if SPLIT_MULTIPAGE_DOC else 1
        tasks_number = (
            full_tasks + 1
            if SPLIT_MULTIPAGE_DOC and len(pages) % MAX_PAGES
            else full_tasks
        )
        for _ in range(tasks_number):
            tasks.append(
                {
                    "file_id": file_for_task["file_id"],
                    "pages": (
                        pages[:MAX_PAGES] if SPLIT_MULTIPAGE_DOC else pages[:]
                    ),
                    "job_id": job_id,
                    "user_id": user["user_id"],
                    "is_validation": is_validation,
                    "status": status,
                    "deadline": deadline,
                }
            )
            if SPLIT_MULTIPAGE_DOC:
                pages[:MAX_PAGES] = []
            else:
                pages[:] = []
        user["pages_number"] -= file_for_task["pages_number"]
        file_for_task["pages_number"] = 0


def find_small_files(
    files: List[Dict[str, int]], user_pages: int
) -> Tuple[List[Dict[str, int]], int]:
    """Find files with the number pages less than the user's load."""
    files_pages = [x["pages_number"] for x in files if x["pages_number"]]
    pages_for_task = []
    user_page_correction = 0
    for pages in files_pages:
        if pages <= user_pages or (user_pages and not SPLIT_MULTIPAGE_DOC):
            pages_for_task.append(pages)
            user_pages -= pages
            if user_pages <= 0:
                user_page_correction = abs(user_pages)
                user_pages = 0
                break
    return find_files_for_task(files, pages_for_task), user_page_correction


def distribute_annotation_partial_files(
    files: List[Dict[str, int]],
    annotators: List[DistributionUser],
    job_id: int,
    status: TaskStatusEnumSchema,
    deadline: Optional[datetime] = None,
) -> List[Task]:
    """Create annotation tasks from partial files. If "SPLIT_MULTIPAGE_DOC"
    environmental variable is set to "true", each task doesn't contain more
    than 50 pages. If page number in file for distribution is greater than 50,
    they will be divided in different tasks respectively.
    """
    annotators = [x for x in annotators if x["pages_number"]]
    files = [x for x in files if x["pages_number"]]
    annotation_tasks = []
    for item in files:
        pages = []
        # field unassigned_pages contains specific unassigned pages in file
        # if this field is not present, all pages if file are unassigned
        pages_to_distribute = item.get(
            "unassigned_pages", list(range(1, item["pages_number"] + 1))
        )
        if not annotators[0]["pages_number"]:
            annotators.pop(0)
        for page in pages_to_distribute:
            if annotators[0]["pages_number"] and (
                len(pages) < MAX_PAGES or not SPLIT_MULTIPAGE_DOC
            ):
                pages.append(page)
            else:
                annotation_tasks.append(
                    {
                        "file_id": item["file_id"],
                        "pages": pages,
                        "job_id": job_id,
                        "user_id": annotators[0]["user_id"],
                        "is_validation": False,
                        "status": status,
                        "deadline": deadline,
                    }
                )
                pages = [page]
            if not annotators[0]["pages_number"]:
                annotators.pop(0)
            annotators[0]["pages_number"] -= 1
        if pages:
            full_tasks = len(pages) // MAX_PAGES if SPLIT_MULTIPAGE_DOC else 1
            tasks_number = (
                full_tasks + 1
                if SPLIT_MULTIPAGE_DOC and len(pages) % MAX_PAGES
                else full_tasks
            )
            for _ in range(tasks_number):
                annotation_tasks.append(
                    {
                        "file_id": item["file_id"],
                        "pages": (
                            pages[:MAX_PAGES]
                            if SPLIT_MULTIPAGE_DOC
                            else pages[:]
                        ),
                        "job_id": job_id,
                        "user_id": annotators[0]["user_id"],
                        "is_validation": False,
                        "status": status,
                        "deadline": deadline,
                    }
                )
                if SPLIT_MULTIPAGE_DOC:
                    pages[:MAX_PAGES] = []
                else:
                    pages[:] = []
    return annotation_tasks


def filter_validation_files_pages(
    validator: DistributionUser,
    annotated_files_pages: AnnotatedFilesPages,
    files_all_pages: Dict[int, Set[int]],
    count_annotator_pages: bool,
) -> Dict[str, List[int]]:
    """For cross-validation checks if there are files and pages for files
    distributed for annotation for this validator. Skips them and left only not
    distributed for annotation files and pages For hierarchical-validation
    skips annotation files and pages check. For each page left:
      - if count_annotator_pages - adds this page to files_for_validation pages
    list if validator has available pages number left. This pages will be added
    to validation task for this validator and file_id. Also removes this page
    from files_all_pages (common for all validators) to track how many pages
    in files left totally.
      - if not count_annotator_pages - adds all remaining pages for this file
    to files_for_validation pages list. This pages will be added to validation
    task for this validator and file_id and removed from files_all_pages to
    track how many pages in files left totally.
    """
    files_for_validation = defaultdict(list)
    for file_id, pages in files_all_pages.items():
        annotated_pages = []
        annotated_files = annotated_files_pages.get(validator["user_id"], [])
        if annotated_files:
            annotated_pages.extend(
                page
                for annotated in annotated_files
                for page in annotated["pages"]
                if annotated["file_id"] == file_id
            )
        for page in pages:
            # If we track validator's page load - stops if no load pages left.
            if count_annotator_pages and not validator["pages_number"]:
                files_all_pages[file_id].difference_update(
                    files_for_validation[file_id]
                )
                return files_for_validation
            # If we don't track validator's page load - adds all file's pages.
            if page not in annotated_pages:
                files_for_validation[file_id].append(page)
                validator["pages_number"] = (
                    validator["pages_number"] - 1
                    if validator["pages_number"] > 0
                    else 0
                )
        files_all_pages[file_id].difference_update(
            files_for_validation[file_id]
        )
    return files_for_validation


def create_partial_validation_tasks(
    annotated_files_pages: AnnotatedFilesPages,
    validators: List[DistributionUser],
    files_all_pages: Dict[int, Set[int]],
    job_id: int,
    validation_tasks: List[Task],
    status: TaskStatusEnumSchema,
    count_annotator_pages: bool,
    deadline: Optional[datetime] = None,
) -> None:
    """Create validation tasks from partial files. For cross-validation also
    checks that for every validator this file's pages were not distributed for
    annotation. If "SPLIT_MULTIPAGE_DOC" environmental variable is set to
    "true", each task doesn't contain more than 50 pages. If page number in
    file for distribution is greater than 50, they will be divided in
    different tasks respectively.
    """
    for validator in validators:
        validation_files_pages = filter_validation_files_pages(
            validator,
            annotated_files_pages,
            files_all_pages,
            count_annotator_pages,
        )
        for file_id, pages in validation_files_pages.items():
            if pages:
                full_tasks = (
                    len(pages) // MAX_PAGES if SPLIT_MULTIPAGE_DOC else 1
                )
                tasks_number = (
                    full_tasks + 1
                    if SPLIT_MULTIPAGE_DOC and len(pages) % MAX_PAGES
                    else full_tasks
                )
                for _ in range(tasks_number):
                    validation_tasks.append(
                        {
                            "file_id": file_id,
                            "pages": (
                                pages[:MAX_PAGES]
                                if SPLIT_MULTIPAGE_DOC
                                else pages[:]
                            ),
                            "job_id": job_id,
                            "user_id": validator["user_id"],
                            "is_validation": True,
                            "status": status,
                            "deadline": deadline,
                        }
                    )
                    if SPLIT_MULTIPAGE_DOC:
                        pages[:MAX_PAGES] = []
                    else:
                        pages[:] = []


def distribute_validation_partial_files(
    annotated_files_pages: AnnotatedFilesPages,
    files: List[Dict[str, int]],
    validators: List[DistributionUser],
    job_id: int,
    tasks_status: TaskStatusEnumSchema,
    deadline: Optional[datetime] = None,
) -> List[Task]:
    """Create validation tasks from partial files."""
    validation_tasks = []
    # 'files_all_pages' is common for all validator and is used to count
    # remaining not distributed for validation pages for every file. Files and
    # pages for each validator are created based on this dict data.
    files_all_pages = {
        item["file_id"]: (
            set(range(1, item["pages_number"] + 1))
            if "unassigned_pages" not in item
            else set(item["unassigned_pages"])
        )
        for item in files
    }
    create_partial_validation_tasks(
        annotated_files_pages,
        validators,
        files_all_pages,
        job_id,
        validation_tasks,
        tasks_status,
        count_annotator_pages=True,
        deadline=deadline,
    )
    # If there are still some remaining not distributed for validation pages -
    # starts distribution algorithm without checking number of remaining pages
    # load for validators (count_annotator_pages parameter == False).
    if any(files_all_pages.values()):
        create_partial_validation_tasks(
            annotated_files_pages,
            validators,
            files_all_pages,
            job_id,
            validation_tasks,
            tasks_status,
            count_annotator_pages=False,
            deadline=deadline,
        )
    return validation_tasks


def find_unassigned_files(
    files: List[File],
) -> Tuple[FilesForDistribution, FilesForDistribution]:
    """
    Find files, that are not fully distributed or not distributed at all.
    If number of distributed pages is equal to number of pages in file,
        then file was fully distributed.
    If number of distributed pages is equal to zero,
        then file was not distributed at all.
    In other cases file was partially distributed, hence we need to find
        unassigned pages.
    """
    annotation_files_to_distribute = []
    validation_files_to_distribute = []

    for f in files:
        if (
            len(f.distributed_annotating_pages) == f.pages_number
            and len(f.distributed_validating_pages) == f.pages_number
        ):
            # whole file was distributed
            continue
        check_file_distribution(
            annotation_files_to_distribute,
            f.distributed_annotating_pages,
            f.file_id,
            f.pages_number,
        )
        check_file_distribution(
            validation_files_to_distribute,
            f.distributed_validating_pages,
            f.file_id,
            f.pages_number,
        )

    return annotation_files_to_distribute, validation_files_to_distribute


def check_file_distribution(
    files_to_distribute: FilesForDistribution,
    distributed_pages: List[int],
    file_id: int,
    pages_number: int,
) -> None:
    """
    Check distribution of file.
    There are two cases:
    1) If number of distributed pages equals zero, file was not distributed
    at all. There are no specific pages for distribution.
    2) Else, file was partially distribute. There are specific pages for
    distribution, they will be added in field 'unassigned_pages' to dict in
    'files_to_distribute' list.
    """
    if len(distributed_pages) == 0:
        # file was not distributed at all
        add_unassigned_file(files_to_distribute, file_id, pages_number)
    else:
        # file was partially distributed
        unassigned_pages = find_unassigned_pages(
            distributed_pages, pages_number
        )
        add_unassigned_file(
            files_to_distribute,
            file_id,
            len(unassigned_pages),
            unassigned_pages,
        )


def find_unassigned_pages(
    assigned_pages: list, pages_amount: int
) -> List[int]:
    """
    Get all pages, that were not distributed.
    """
    return [
        page
        for page in range(1, pages_amount + 1)
        if page not in assigned_pages
    ]


def add_unassigned_file(
    files_to_distribute: FilesForDistribution,
    file_id: int,
    pages_number: int,
    unassigned_pages: Optional[List[int]] = None,
) -> None:
    """
    Add file, that needs to be distributed, to array.
    If unassigned_pages array is present, it means, that file
    partially distributed and this array consists of
    unassigned pages,
    otherwise whole file was not distributed.
    For example:
    unassigned_pages = [3, 4, 6] means, that these pages
    are unassigned and should be distributed.
    """
    f = {"file_id": file_id, "pages_number": pages_number}
    if unassigned_pages:
        f["unassigned_pages"] = unassigned_pages
    files_to_distribute.append(f)


def prepare_response(
    deadline: Optional[datetime],
    annotation_files_to_distribute: FilesForDistribution,
    validation_files_to_distribute: FilesForDistribution,
    annotators: List[User],
    validators: List[User],
    job_id: int,
    validation_type: ValidationSchema,
    db: Session,
    annotation_tasks_status: TaskStatusEnumSchema = TaskStatusEnumSchema.pending,  # noqa E501
    validation_tasks_status: TaskStatusEnumSchema = TaskStatusEnumSchema.pending,  # noqa E501
    already_created_tasks: List[dict] = None,
):
    annotation_tasks = [
        task
        for task in distribute(
            db=db,
            files=annotation_files_to_distribute,
            annotators=annotators,
            validators=validators,
            job_id=job_id,
            validation_type=validation_type,
            validation_files_to_distribute=validation_files_to_distribute,
            annotation_tasks_status=annotation_tasks_status,
            validation_tasks_status=validation_tasks_status,
            already_created_tasks=already_created_tasks,
            deadline=deadline,
        )
    ]
    return annotation_tasks


async def redistribute(
    db: Session, token: str, x_current_tenant: str, job: Job
):
    """Delete unstarted tasks and distribute files without assignment."""
    job_old_tasks = (
        db.query(ManualAnnotationTask)
        .filter(ManualAnnotationTask.job_id == job.job_id)
        .all()
    )
    tasks_to_delete = get_tasks_to_delete(job_old_tasks)
    delete_tasks(db, tasks_to_delete)
    db.flush()

    files = [
        {"file_id": job_file.file_id, "pages_number": job_file.pages_number}
        for job_file in job.files
    ]
    pages_in_work = get_pages_in_work(set(job_old_tasks), tasks_to_delete)

    distribute(
        db,
        files,
        job.annotators,
        job.validators,
        job.job_id,
        job.validation_type,
        deadline=job.deadline,
        extensive_coverage=job.extensive_coverage,
        pages_in_work=pages_in_work,
    )

    job_new_tasks = sorted(
        (
            db.query(ManualAnnotationTask)
            .filter(ManualAnnotationTask.job_id == job.job_id)
            .all()
        ),
        key=lambda x: len(x.pages),
        reverse=True,
    )

    if job.status == JobStatusEnumSchema.in_progress:
        set_task_statuses(job, job_new_tasks)
        db.flush()

    if all(
        job_task.status == TaskStatusEnumSchema.finished
        for job_task in job_new_tasks
    ):
        # finish job
        try:
            await update_job_status(
                job.callback_url,
                JobStatusEnumSchema.finished,
                x_current_tenant,
                token,
            )
        except JobUpdateException as exc:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error: connection error ({exc.exc_info})",
            )
        job.status = JobStatusEnumSchema.finished
