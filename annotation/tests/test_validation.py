from typing import List
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import or_

from app.annotations import row_to_dict
from app.models import AnnotatedDoc, File, Job, ManualAnnotationTask, User
from app.schemas import (
    AnnotationAndValidationActionsSchema,
    FileStatusEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from app.tasks.validation import (
    _find_annotators_for_failed_pages,
    check_user_job_action,
    check_user_job_belonging,
    check_uuid,
    construct_tasks,
    create_annotation_tasks,
    create_validation_tasks,
    find_initial_annotators,
    get_annotators_revisions,
)
from tests.consts import FINISH_TASK_PATH
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app
from tests.test_finish_task import check_files_finished_pages
from tests.test_post import check_files_distributed_pages

client = TestClient(app)

BAD_UUID = "bad_uuid"
ANNOTATORS = [
    User(
        user_id=UUID("10b68bc8-468f-43dc-8981-106b660a8578"),
        default_load=100,
        overall_load=0,
    ),
    User(
        user_id=UUID("20b68bc8-468f-43dc-8981-106b660a8578"),
        default_load=100,
        overall_load=0,
    ),
    User(
        user_id=UUID("30b68bc8-468f-43dc-8981-106b660a8578"),
        default_load=100,
        overall_load=0,
    ),
    User(
        user_id=UUID("40b68bc8-468f-43dc-8981-106b660a8578"),
        default_load=100,
        overall_load=0,
    ),
]
JOBS = [
    Job(
        job_id=1,
        callback_url="http://www.test.com",
        annotators=[
            ANNOTATORS[0],
            ANNOTATORS[1],
            ANNOTATORS[2],
            ANNOTATORS[3],
        ],
        owners=[ANNOTATORS[3]],
        is_auto_distribution=False,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
        validation_type=ValidationSchema.cross,
    ),
    Job(
        job_id=2,
        callback_url="http://www.test.com",
        annotators=[
            ANNOTATORS[0],
        ],
        validators=[ANNOTATORS[1]],
        is_auto_distribution=False,
        deadline="2021-10-19T01:01:02",
        tenant=TEST_TENANT,
        validation_type=ValidationSchema.hierarchical,
    ),
]
FILES = [
    File(
        file_id=1,
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=5,
        distributed_annotating_pages=[1, 2, 3, 4, 5],
        annotated_pages=[1, 2, 3, 4, 5],
        distributed_validating_pages=[1, 2, 3, 4, 5],
        validated_pages=[],
        status=FileStatusEnumSchema.annotated,
    ),
    File(
        file_id=2,
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=5,
        distributed_annotating_pages=[1, 2, 3, 4, 5],
        annotated_pages=[1, 2, 3, 4, 5],
        distributed_validating_pages=[1, 2, 3, 4, 5],
        validated_pages=[],
        status=FileStatusEnumSchema.annotated,
    ),
    File(
        file_id=3,
        tenant=TEST_TENANT,
        job_id=JOBS[1].job_id,
        pages_number=5,
        distributed_annotating_pages=[1, 2, 3, 4, 5],
        annotated_pages=[1, 2, 3, 4, 5],
        distributed_validating_pages=[1, 2, 3, 4, 5],
        validated_pages=[],
        status=FileStatusEnumSchema.annotated,
    ),
    File(
        file_id=4,
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=2,
        distributed_annotating_pages=[1, 2],
        annotated_pages=[1, 2],
        distributed_validating_pages=[1, 2],
        validated_pages=[],
        status=FileStatusEnumSchema.annotated,
    ),
]
TASKS = [
    ManualAnnotationTask(
        id=100,
        deadline=JOBS[0].deadline,
        file_id=FILES[0].file_id,
        is_validation=False,
        job_id=FILES[0].job_id,
        pages=[1, 2, 3],
        status=TaskStatusEnumSchema.finished,
        user_id=ANNOTATORS[0].user_id,
    ),  # annotation task for first job, first file, first user
    ManualAnnotationTask(
        id=101,
        deadline=JOBS[0].deadline,
        file_id=FILES[0].file_id,
        is_validation=False,
        job_id=FILES[0].job_id,
        pages=[4, 5],
        status=TaskStatusEnumSchema.finished,
        user_id=ANNOTATORS[1].user_id,
    ),  # annotation task for first job, first file, second user
    ManualAnnotationTask(
        id=102,
        deadline=JOBS[0].deadline,
        file_id=FILES[1].file_id,
        is_validation=False,
        job_id=FILES[1].job_id,
        pages=[1, 2, 3],
        status=TaskStatusEnumSchema.finished,
        user_id=ANNOTATORS[0].user_id,
    ),  # annotation task for first job, second file, first user
    ManualAnnotationTask(
        id=103,
        deadline=JOBS[0].deadline,
        file_id=FILES[1].file_id,
        is_validation=False,
        job_id=FILES[1].job_id,
        pages=[4, 5],
        status=TaskStatusEnumSchema.finished,
        user_id=ANNOTATORS[0].user_id,
    ),  # annotation task for first job, second file, first user
    ManualAnnotationTask(
        id=104,
        deadline=JOBS[0].deadline,
        file_id=FILES[0].file_id,
        is_validation=True,
        job_id=FILES[0].job_id,
        pages=[1, 2, 3, 4, 5],
        status=TaskStatusEnumSchema.in_progress,
        user_id=ANNOTATORS[2].user_id,
    ),  # validation task for first job, first file, third user
    ManualAnnotationTask(
        id=105,
        deadline=JOBS[0].deadline,
        file_id=FILES[1].file_id,
        is_validation=True,
        job_id=FILES[1].job_id,
        pages=[1, 2, 3],
        status=TaskStatusEnumSchema.in_progress,
        user_id=ANNOTATORS[3].user_id,
    ),  # validation task for first job, second file, fourth user
    ManualAnnotationTask(
        id=106,
        deadline=JOBS[0].deadline,
        file_id=FILES[1].file_id,
        is_validation=True,
        job_id=FILES[1].job_id,
        pages=[4, 5],
        status=TaskStatusEnumSchema.in_progress,
        user_id=ANNOTATORS[3].user_id,
    ),  # validation task for first job, second file, fourth user
    ManualAnnotationTask(
        id=107,
        deadline=JOBS[1].deadline,
        file_id=FILES[2].file_id,
        is_validation=False,
        job_id=FILES[2].job_id,
        pages=[1, 2, 3, 4, 5],
        status=TaskStatusEnumSchema.finished,
        user_id=ANNOTATORS[0].user_id,
    ),  # annotation task for second job, third file, first user
    ManualAnnotationTask(
        id=108,
        deadline=JOBS[1].deadline,
        file_id=FILES[2].file_id,
        is_validation=True,
        job_id=FILES[2].job_id,
        pages=[1, 2, 3, 4, 5],
        status=TaskStatusEnumSchema.in_progress,
        user_id=ANNOTATORS[1].user_id,
    ),  # validation task for second job, third file, second user
    ManualAnnotationTask(
        id=109,
        deadline=JOBS[0].deadline,
        file_id=FILES[0].file_id,
        is_validation=True,
        job_id=FILES[0].job_id,
        pages=[1, 2, 3, 4, 5],
        status=TaskStatusEnumSchema.in_progress,
        user_id=ANNOTATORS[2].user_id,
    ),  # validation task for first job, first file, third user
    # but it was not completed
    ManualAnnotationTask(
        id=110,
        deadline=JOBS[0].deadline,
        file_id=FILES[0].file_id,
        is_validation=False,
        job_id=FILES[0].job_id,
        pages=[1, 2, 3, 4, 5],
        status=TaskStatusEnumSchema.in_progress,
        user_id=ANNOTATORS[2].user_id,
    ),  # annotation task for first job, first file, third user
    # but it was not completed
    ManualAnnotationTask(
        id=111,
        deadline=JOBS[0].deadline,
        file_id=FILES[3].file_id,
        is_validation=False,
        job_id=FILES[3].job_id,
        pages=[1, 2],
        status=TaskStatusEnumSchema.finished,
        user_id=ANNOTATORS[0].user_id,
    ),  # annotation task for first job, fourth file, first user
    ManualAnnotationTask(
        id=112,
        deadline=JOBS[0].deadline,
        file_id=FILES[3].file_id,
        is_validation=True,
        job_id=FILES[3].job_id,
        pages=[1],
        status=TaskStatusEnumSchema.in_progress,
        user_id=ANNOTATORS[1].user_id,
    ),  # validation task for first job, fourth file, first user
    ManualAnnotationTask(
        id=113,
        deadline=JOBS[0].deadline,
        file_id=FILES[3].file_id,
        is_validation=True,
        job_id=FILES[3].job_id,
        pages=[2],
        status=TaskStatusEnumSchema.in_progress,
        user_id=ANNOTATORS[1].user_id,
    ),  # validation task for first job, fourth file, first user
]
DOCS = [
    AnnotatedDoc(
        revision="1",
        user=TASKS[0].user_id,
        pipeline=None,
        file_id=TASKS[0].file_id,
        job_id=TASKS[0].job_id,
        pages={"1": "11", "2": "21"},
        validated=[],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        task_id=TASKS[0].id,
        date="2004-10-19T10:01:00",
    ),  # first revision of annotation task for
    # first job, first file, first user
    AnnotatedDoc(
        revision="2",
        user=TASKS[0].user_id,
        pipeline=None,
        file_id=TASKS[0].file_id,
        job_id=TASKS[0].job_id,
        pages={"2": "22", "3": "31"},
        validated=[],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        task_id=TASKS[0].id,
        date="2004-10-19T10:01:01",
    ),  # second revision of annotation task for
    # first job, first file, first user
    AnnotatedDoc(
        revision="3",
        user=TASKS[1].user_id,
        pipeline=None,
        file_id=TASKS[1].file_id,
        job_id=TASKS[1].job_id,
        pages={"4": "41", "5": "51"},
        validated=[],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        task_id=TASKS[1].id,
        date="2004-10-19T10:01:02",
    ),  # first revision of annotation task for
    # first job, first file, second user
    AnnotatedDoc(
        revision="4",
        user=TASKS[1].user_id,
        pipeline=None,
        file_id=TASKS[1].file_id,
        job_id=TASKS[1].job_id,
        pages={"4": "42", "5": "52"},
        validated=[],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        task_id=TASKS[1].id,
        date="2004-10-19T10:01:03",
    ),  # second revision of annotation task for
    # first job, first file, second user
    AnnotatedDoc(
        revision="5",
        user=TASKS[2].user_id,
        pipeline=None,
        file_id=TASKS[2].file_id,
        job_id=TASKS[2].job_id,
        pages={"1": "11", "2": "21", "3": "31"},
        validated=[],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        task_id=TASKS[2].id,
        date="2004-10-19T10:01:00",
    ),  # first revision of annotation task for
    # first job, second file, first user
    AnnotatedDoc(
        revision="6",
        user=TASKS[3].user_id,
        pipeline=None,
        file_id=TASKS[3].file_id,
        job_id=TASKS[3].job_id,
        pages={"4": "41", "5": "51"},
        validated=[],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        task_id=TASKS[3].id,
        date="2004-10-19T10:01:00",
    ),  # first revision of annotation task for
    # first job, second file, first user
    AnnotatedDoc(
        revision="7",
        user=TASKS[4].user_id,
        pipeline=None,
        file_id=TASKS[4].file_id,
        job_id=TASKS[4].job_id,
        pages={},
        validated=[1, 2, 3],
        failed_validation_pages=[4, 5],
        tenant=TEST_TENANT,
        task_id=TASKS[4].id,
        date="2004-10-19T10:01:00",
    ),  # first revision of validation task for
    # first job, first file, third user
    AnnotatedDoc(
        revision="8",
        user=TASKS[4].user_id,
        pipeline=None,
        file_id=TASKS[4].file_id,
        job_id=TASKS[4].job_id,
        pages={"1": "12", "4": "42"},
        validated=[4, 5],
        failed_validation_pages=[1, 2, 3],
        tenant=TEST_TENANT,
        task_id=TASKS[4].id,
        date="2004-10-19T10:01:01",
    ),  # second revision of validation task for
    # first job, first file, third user
    AnnotatedDoc(
        revision="9",
        user=TASKS[5].user_id,
        pipeline=None,
        file_id=TASKS[5].file_id,
        job_id=TASKS[5].job_id,
        pages={"2": "21"},
        validated=[1, 3],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        task_id=TASKS[5].id,
        date="2004-10-19T10:01:00",
    ),  # first revision of validation task for
    # first job, second file, fourth user
    AnnotatedDoc(
        revision="10",
        user=TASKS[5].user_id,
        pipeline=None,
        file_id=TASKS[5].file_id,
        job_id=TASKS[5].job_id,
        pages={"2": "21"},
        validated=[],
        failed_validation_pages=[1, 3],
        tenant=TEST_TENANT,
        task_id=TASKS[5].id,
        date="2004-10-19T10:01:01",
    ),  # second revision of validation task for
    # first job, second file, fourth user
    AnnotatedDoc(
        revision="11",
        user=TASKS[6].user_id,
        pipeline=None,
        file_id=TASKS[6].file_id,
        job_id=TASKS[6].job_id,
        pages={},
        validated=[4, 5],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        task_id=TASKS[6].id,
        date="2004-10-19T10:01:00",
    ),  # first revision of validation task for
    # first job, second file, fourth user
    AnnotatedDoc(
        revision="12",
        user=TASKS[7].user_id,
        pipeline=None,
        file_id=TASKS[7].file_id,
        job_id=TASKS[7].job_id,
        pages={"1": "11", "2": "21", "3": "31", "4": "41", "5": "51"},
        validated=[],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        task_id=TASKS[7].id,
        date="2004-10-19T10:01:00",
    ),  # first revision of annotation task for
    # second job, third file, first user
    AnnotatedDoc(
        revision="13",
        user=TASKS[8].user_id,
        pipeline=None,
        file_id=TASKS[8].file_id,
        job_id=TASKS[8].job_id,
        pages={"1": "11", "2": "21"},
        validated=[3],
        failed_validation_pages=[4, 5],
        tenant=TEST_TENANT,
        task_id=TASKS[8].id,
        date="2004-10-19T10:01:00",
    ),  # first revision of annotation task for
    # second job, third file, second user
    AnnotatedDoc(
        revision="14",
        user=TASKS[11].user_id,
        pipeline=None,
        file_id=TASKS[11].file_id,
        job_id=TASKS[11].job_id,
        pages={"1": "11", "2": "21"},
        validated=[],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        task_id=TASKS[11].id,
        date="2004-10-19T10:01:00",
    ),  # first revision of annotation task for
    # first job, fourth file, first user
    AnnotatedDoc(
        revision="15",
        user=TASKS[12].user_id,
        pipeline=None,
        file_id=TASKS[12].file_id,
        job_id=TASKS[12].job_id,
        pages={
            "1": "11",
        },
        validated=[],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        task_id=TASKS[12].id,
        date="2004-10-19T10:01:00",
    ),  # first revision of validation task for
    # first job, fourth file, first user
    AnnotatedDoc(
        revision="16",
        user=TASKS[13].user_id,
        pipeline=None,
        file_id=TASKS[13].file_id,
        job_id=TASKS[13].job_id,
        pages={},
        validated=[],
        failed_validation_pages=[2],
        tenant=TEST_TENANT,
        task_id=TASKS[13].id,
        date="2004-10-19T10:01:00",
    ),  # first revision of validation task for
    # first job, fourth file, first user
]


def prepare_result(tasks: List[ManualAnnotationTask]) -> List[dict]:
    actual_tasks = []
    for task in tasks:
        actual_task = row_to_dict(task)
        del actual_task["id"]
        actual_tasks.append(actual_task)
    return actual_tasks


@pytest.mark.integration
@pytest.mark.parametrize(
    ["file_id", "job_id", "task_id", "expected_result"],
    [
        # DOCS[6] is validation revision, so in this case
        # func should find all annotations for given file_id
        # job_id and not task_id
        (
            DOCS[6].file_id,
            DOCS[6].job_id,
            DOCS[6].task_id,
            [row_to_dict(rev) for rev in DOCS[:4]],
        ),
        (100, 100, 1, []),
    ],
)
def test_get_annotators_revisions(
    db_validation_end, file_id, job_id, task_id, expected_result
):
    actual_result = get_annotators_revisions(
        db_validation_end, file_id, job_id, task_id
    )
    actual_result = [row_to_dict(rev) for rev in actual_result]
    assert actual_result == expected_result


EXPECTED_INITIAL_ANNOTATORS = [
    {DOCS[0].user: {1, 2, 3}, DOCS[2].user: {4, 5}},
    {DOCS[4].user: {1, 2, 3, 4, 5}},
]


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["revisions", "pages", "expected_result"],
    [
        (DOCS[:4], {1, 2, 3, 4, 5}, EXPECTED_INITIAL_ANNOTATORS[0]),
        (DOCS[4:6], {1, 2, 3, 4, 5}, EXPECTED_INITIAL_ANNOTATORS[1]),
        (DOCS[4:6], {1, 2, 3, 4, 5, 6, 7}, EXPECTED_INITIAL_ANNOTATORS[1]),
        (DOCS[6:7], {1, 2, 3, 4, 5}, {}),
    ],
)
def test_find_initial_annotators(revisions, pages, expected_result):
    actual_result = find_initial_annotators(revisions, pages)
    assert actual_result == expected_result


TASK_FAILED_PAGES = ManualAnnotationTask(
    id=114,
    deadline=JOBS[0].deadline,
    file_id=FILES[0].file_id,
    is_validation=False,
    job_id=FILES[0].job_id,
    pages=[1, 2, 3],
    status=TaskStatusEnumSchema.finished,
    user_id=ANNOTATORS[1].user_id,
)
ANNOTATION_FAILED_PAGES = AnnotatedDoc(
    revision="17",
    user=TASK_FAILED_PAGES.user_id,
    pipeline=None,
    file_id=TASK_FAILED_PAGES.file_id,
    job_id=TASK_FAILED_PAGES.job_id,
    pages={"1": "15", "2": "18", "3": "20", "4": "54", "5": "76"},
    validated=[],
    failed_validation_pages=[],
    tenant=TEST_TENANT,
    task_id=TASK_FAILED_PAGES.id,
    date="2004-11-19T10:01:00",
)


@pytest.mark.integration
def test_find_annotators_for_failed_pages(
    prepare_db_find_annotators_for_failed_pages,
):
    """
    Case: there are two revisions for the same file pages
    created for one job. If the first annotator who created
    the revision earlier is deleted,
    there should be no error raised since
    the second annotator`s revision is the most up-to-date
    and the second annotator is still in a DB.
    """
    revisions = get_annotators_revisions(
        prepare_db_find_annotators_for_failed_pages,
        DOCS[7].file_id,
        DOCS[7].job_id,
        DOCS[7].task_id,
    )
    annotators_for_failed_pages = _find_annotators_for_failed_pages(
        revisions, set(DOCS[7].failed_validation_pages)
    )

    # annotators_for_failed_pages returns dict {page: user}
    # where each page corresponds with the last user who annotated it
    expected_result = {
        1: ANNOTATORS[1].user_id,
        2: ANNOTATORS[1].user_id,
        3: ANNOTATORS[1].user_id,
    }
    assert annotators_for_failed_pages == expected_result


EXPECTED_TASKS = [
    [
        {
            "file_id": DOCS[0].file_id,
            "pages": EXPECTED_INITIAL_ANNOTATORS[0][DOCS[0].user],
            "job_id": DOCS[0].job_id,
            "user_id": DOCS[0].user,
            "is_validation": False,
            "deadline": JOBS[0].deadline,
            "status": TaskStatusEnumSchema.ready,
        },
        {
            "file_id": DOCS[0].file_id,
            "pages": EXPECTED_INITIAL_ANNOTATORS[0][DOCS[2].user],
            "job_id": DOCS[0].job_id,
            "user_id": DOCS[2].user,
            "is_validation": False,
            "deadline": JOBS[0].deadline,
            "status": TaskStatusEnumSchema.ready,
        },
    ],
    [
        {
            "file_id": DOCS[4].file_id,
            "pages": EXPECTED_INITIAL_ANNOTATORS[1][DOCS[4].user],
            "job_id": DOCS[4].job_id,
            "user_id": DOCS[4].user,
            "is_validation": False,
            "deadline": JOBS[0].deadline,
            "status": TaskStatusEnumSchema.ready,
        },
    ],
    [
        {
            "file_id": DOCS[4].file_id,
            "pages": EXPECTED_INITIAL_ANNOTATORS[1][DOCS[4].user],
            "job_id": DOCS[4].job_id,
            "user_id": DOCS[4].user,
            "is_validation": True,
            "deadline": JOBS[1].deadline,
            "status": TaskStatusEnumSchema.pending,
        },
    ],
]


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "users",
        "job_id",
        "file_id",
        "is_validation",
        "deadline",
        "status",
        "expected_result",
    ],
    [
        (
            EXPECTED_INITIAL_ANNOTATORS[0],
            DOCS[0].job_id,
            DOCS[0].file_id,
            False,
            JOBS[0].deadline,
            TaskStatusEnumSchema.ready,
            EXPECTED_TASKS[0],
        ),
        (
            EXPECTED_INITIAL_ANNOTATORS[1],
            DOCS[4].job_id,
            DOCS[4].file_id,
            False,
            JOBS[0].deadline,
            TaskStatusEnumSchema.ready,
            EXPECTED_TASKS[1],
        ),
        (
            EXPECTED_INITIAL_ANNOTATORS[1],
            DOCS[4].job_id,
            DOCS[4].file_id,
            True,
            JOBS[1].deadline,
            TaskStatusEnumSchema.pending,
            EXPECTED_TASKS[2],
        ),
    ],
)
def test_construct_tasks(
    users, job_id, file_id, is_validation, deadline, status, expected_result
):
    actual_result = construct_tasks(
        users, job_id, file_id, is_validation, deadline, status
    )
    assert actual_result == expected_result


@pytest.mark.unittest
def test_check_uuid():
    user_id = "10b68bc8-468f-43dc-8981-106b660a8578"
    expected_result = UUID(user_id)
    actual_result = check_uuid(user_id)
    assert actual_result == expected_result


@pytest.mark.unittest
def test_check_uuid_exception():
    user_id = BAD_UUID
    with pytest.raises(HTTPException):
        check_uuid(user_id)


@pytest.mark.integration
@pytest.mark.parametrize(
    ["user_id", "job_id", "only_owner", "expected_result"],
    [
        # user belongs to job
        (ANNOTATORS[0].user_id, JOBS[0].job_id, False, True),
        # user is not owner
        (ANNOTATORS[0].user_id, JOBS[0].job_id, True, False),
        # user does not belong to job
        (ANNOTATORS[3].user_id, JOBS[1].job_id, False, False),
        # user is owner
        (ANNOTATORS[3].user_id, JOBS[0].job_id, True, True),
    ],
)
def test_check_user_job_belonging(
    db_validation_end, user_id, job_id, only_owner, expected_result
):
    actual_result = check_user_job_belonging(
        db_validation_end, user_id, job_id, only_owner
    )
    assert actual_result == expected_result


@pytest.mark.integration
@pytest.mark.parametrize(
    ["user_id", "job_id", "owner_check", "expected_result"],
    [
        # user is not owner
        (ANNOTATORS[0].user_id, JOBS[0].job_id, True, False),
        # user does not belong to job
        (ANNOTATORS[3].user_id, JOBS[1].job_id, False, False),
    ],
)
def test_check_user_job_action(
    db_validation_end, user_id, job_id, owner_check, expected_result
):
    with pytest.raises(HTTPException):
        check_user_job_action(db_validation_end, user_id, job_id, owner_check)


EXPECTED_DB_TASKS = [
    [
        {
            "file_id": TASKS[5].file_id,
            "pages": [1, 2, 3, 4, 5],
            "job_id": TASKS[5].job_id,
            "user_id": str(TASKS[2].user_id),  # initial user
            "is_validation": False,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[5].file_id,
            "pages": [1],
            "job_id": TASKS[5].job_id,
            "user_id": str(ANNOTATORS[1].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[5].file_id,
            "pages": [2],
            "job_id": TASKS[5].job_id,
            "user_id": str(ANNOTATORS[2].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[5].file_id,
            "pages": [3],
            "job_id": TASKS[5].job_id,
            "user_id": str(ANNOTATORS[3].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[5].file_id,
            "pages": [4, 5],
            "job_id": TASKS[5].job_id,
            "user_id": str(ANNOTATORS[1].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
    ],
    [
        {
            "file_id": TASKS[0].file_id,
            "pages": [1, 2, 3],
            "job_id": FILES[0].job_id,
            "user_id": str(TASKS[0].user_id),  # initial user
            "is_validation": False,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[1].file_id,
            "pages": [4, 5],
            "job_id": FILES[1].job_id,
            "user_id": str(TASKS[1].user_id),  # initial user
            "is_validation": False,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[1].file_id,
            "pages": [4, 5],
            "job_id": 1,
            "user_id": str(ANNOTATORS[0].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[1].file_id,
            "pages": [1],
            "job_id": FILES[1].job_id,
            "user_id": str(ANNOTATORS[1].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[1].file_id,
            "pages": [2],
            "job_id": FILES[1].job_id,
            "user_id": str(ANNOTATORS[2].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[1].file_id,
            "pages": [3],
            "job_id": FILES[1].job_id,
            "user_id": str(ANNOTATORS[3].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
    ],
    [
        {
            "file_id": TASKS[7].file_id,
            "pages": [1, 2, 3, 4, 5],
            "job_id": TASKS[7].job_id,
            "user_id": str(TASKS[7].user_id),  # initial user
            "is_validation": False,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[1].deadline,
        },
        {
            "file_id": TASKS[8].file_id,
            "pages": [1, 2, 3, 4, 5],
            "job_id": TASKS[8].job_id,
            "user_id": str(TASKS[8].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[1].deadline,
        },
    ],
    [
        {
            "file_id": TASKS[4].file_id,
            "pages": [1, 2, 3, 4, 5],
            "job_id": TASKS[4].job_id,
            "user_id": str(ANNOTATORS[0].user_id),
            "is_validation": False,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[4].file_id,
            "pages": [1],
            "job_id": TASKS[4].job_id,
            "user_id": str(ANNOTATORS[1].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[4].file_id,
            "pages": [2],
            "job_id": TASKS[4].job_id,
            "user_id": str(ANNOTATORS[2].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[4].file_id,
            "pages": [3],
            "job_id": TASKS[4].job_id,
            "user_id": str(ANNOTATORS[3].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[4].file_id,
            "pages": [4, 5],
            "job_id": TASKS[4].job_id,
            "user_id": str(ANNOTATORS[1].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
    ],
]


@pytest.mark.integration
@pytest.mark.parametrize(
    ["user", "task_id", "failed", "file_id", "job", "expected_tasks"],
    [
        (
            # this test is for tasks with first job, second file,
            # first user (annotator), fourth user (validator)
            # annotation tasks should be assigned to initial user,
            # validation tasks will be distributed automatically
            AnnotationAndValidationActionsSchema.initial.value,
            TASKS[5].id,  # validation task for pages [1, 2, 3, 4, 5]
            # two annotation tasks (2, 3) for pages [1, 2, 3, 4, 5],
            # tasks are assigned to the same (first) user
            {1, 2, 3, 4, 5},
            TASKS[5].file_id,
            JOBS[0],  # cross validation
            EXPECTED_DB_TASKS[0],
        ),
        (
            # this test is for tasks with first job, first file,
            # first, second users (annotators), third user (validator)
            # annotation tasks should be assigned to initial user,
            # validation tasks will be distributed automatically
            AnnotationAndValidationActionsSchema.initial.value,
            TASKS[4].id,  # validation task for pages [1, 2, 3, 4, 5]
            # two annotation tasks (0, 1) for pages [1, 2, 3, 4, 5],
            # tasks are assigned to the first and second users
            {1, 2, 3, 4, 5},
            TASKS[4].file_id,
            JOBS[0],  # cross validation
            EXPECTED_DB_TASKS[1],
        ),
        (
            # this test is for tasks with second job, third file,
            # first user (annotator), second user (validator)
            # annotation tasks should be assigned to initial user,
            # validation tasks will be distributed automatically
            AnnotationAndValidationActionsSchema.initial.value,
            TASKS[8].id,  # validation task for pages [1, 2, 3, 4, 5]
            # one annotation task (7) for pages [1, 2, 3, 4, 5],
            # task is assigned to the first user
            {1, 2, 3, 4, 5},
            TASKS[7].file_id,
            JOBS[1],  # hierarchical validation
            EXPECTED_DB_TASKS[2],
        ),
        (
            # this test is for tasks with first job, second file,
            # first user (annotator), fourth user (validator)
            # annotation tasks should be assigned to specific user,
            # validation tasks will be distributed automatically
            str(ANNOTATORS[0].user_id),
            TASKS[5].id,  # validation task for pages [1, 2, 3, 4, 5]
            # two annotation tasks (2, 3) for pages [1, 2, 3, 4, 5],
            # tasks are assigned to the same (first) user
            {1, 2, 3, 4, 5},
            TASKS[5].file_id,
            JOBS[0],  # cross validation
            EXPECTED_DB_TASKS[0],
        ),
        (
            # this test is for tasks with first job, first file,
            # first, second users (annotators), third user (validator)
            # annotation tasks should be assigned to specific user,
            # validation tasks will be distributed automatically
            str(ANNOTATORS[0].user_id),
            TASKS[4].id,  # validation task for pages [1, 2, 3, 4, 5]
            # two annotation tasks (0, 1) for pages [1, 2, 3, 4, 5],
            # tasks are assigned to the first and second users
            {1, 2, 3, 4, 5},
            TASKS[4].file_id,
            JOBS[0],  # cross validation
            EXPECTED_DB_TASKS[3],
        ),
        (
            # this test is for tasks with second job, third file,
            # first user (annotator), second user (validator)
            # annotation tasks should be assigned to specific user,
            # validation tasks will be distributed automatically
            str(TASKS[7].user_id),
            TASKS[8].id,  # validation task for pages [1, 2, 3, 4, 5]
            # one annotation task (7) for pages [1, 2, 3, 4, 5],
            # task is assigned to the first user
            {1, 2, 3, 4, 5},
            TASKS[7].file_id,
            JOBS[1],  # hierarchical validation
            EXPECTED_DB_TASKS[2],
        ),
        (
            None,
            TASKS[8].id,  # validation task for pages [1, 2, 3, 4, 5]
            # one annotation task (7) for pages [1, 2, 3, 4, 5],
            # task is assigned to the first user
            TASKS[7].pages,
            TASKS[7].file_id,
            JOBS[1],  # hierarchical validation
            [],
        ),
    ],
)
def test_create_annotation_tasks_initial_and_specific(
    db_validation_end, user, task_id, failed, file_id, job, expected_tasks
):
    create_annotation_tasks(
        annotation_user_for_failed_pages=user,
        task_id=task_id,
        db=db_validation_end,
        failed=failed,
        file_id=file_id,
        job=job,
    )
    db_validation_end.commit()

    tasks = (
        db_validation_end.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.file_id == file_id,
            ManualAnnotationTask.job_id == job.job_id,
            or_(
                ManualAnnotationTask.status == TaskStatusEnumSchema.pending,
                ManualAnnotationTask.status == TaskStatusEnumSchema.ready,
            ),
        )
        .all()
    )
    actual_tasks = prepare_result(tasks)

    assert actual_tasks == expected_tasks


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_id", "failed", "file_id", "job", "expected_tasks_number"],
    [
        (
            # this test is for tasks with first job, second file,
            # first user (annotator), fourth user (validator)
            # annotation tasks should be distributed automatically,
            # validation tasks will be distributed automatically
            TASKS[5].id,  # validation task for pages [1, 2, 3, 4, 5]
            # two annotation tasks (2, 3) for pages [1, 2, 3, 4, 5],
            # tasks are assigned to the same (first) user
            {1, 2, 3, 4, 5},
            TASKS[5].file_id,
            JOBS[0],  # cross validation
            8,
        ),
        (
            # this test is for tasks with second job, third file,
            # first user (annotator), second user (validator)
            # annotation tasks should be distributed automatically,
            # validation tasks will be distributed automatically
            TASKS[8].id,  # validation task for pages [1, 2, 3, 4, 5]
            # one annotation task (7) for pages [1, 2, 3, 4, 5],
            # task is assigned to the first user
            {1, 2, 3, 4, 5},
            TASKS[7].file_id,
            JOBS[1],  # hierarchical validation
            2,
        ),
    ],
)
def test_create_annotation_tasks_auto(
    db_validation_end,
    task_id,
    failed,
    file_id,
    job,
    expected_tasks_number,
):
    create_annotation_tasks(
        AnnotationAndValidationActionsSchema.auto,
        task_id=task_id,
        db=db_validation_end,
        failed=failed,
        file_id=file_id,
        job=job,
    )
    db_validation_end.commit()

    actual_tasks_number = (
        db_validation_end.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.file_id == file_id,
            ManualAnnotationTask.job_id == job.job_id,
            or_(
                ManualAnnotationTask.status == TaskStatusEnumSchema.pending,
                ManualAnnotationTask.status == TaskStatusEnumSchema.ready,
            ),
        )
        .count()
    )

    assert actual_tasks_number == expected_tasks_number


EXPECTED_DB_VALIDATION_TASKS = [
    [
        {
            "file_id": TASKS[5].file_id,
            "pages": [1],
            "job_id": TASKS[5].job_id,
            "user_id": str(ANNOTATORS[0].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[5].file_id,
            "pages": [2, 3],
            "job_id": TASKS[5].job_id,
            "user_id": str(ANNOTATORS[1].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[5].file_id,
            "pages": [4, 5],
            "job_id": TASKS[5].job_id,
            "user_id": str(ANNOTATORS[2].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[0].deadline,
        },
    ],
    [
        {
            "file_id": TASKS[8].file_id,
            "pages": [1, 2, 3],
            "job_id": TASKS[8].job_id,
            "user_id": str(ANNOTATORS[1].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[1].deadline,
        },
    ],
    [
        {
            "file_id": TASKS[5].file_id,
            "pages": [1, 2, 3, 4, 5],
            "job_id": TASKS[5].job_id,
            "user_id": str(ANNOTATORS[0].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[0].deadline,
        },
    ],
]


@pytest.mark.integration
@pytest.mark.parametrize(
    ["user", "annotated", "file_id", "job", "user_id", "expected_tasks"],
    [
        (
            # this test is for tasks with first job, second file,
            # first user (annotator), fourth user (validator)
            # validation tasks should be distributed automatically
            AnnotationAndValidationActionsSchema.auto.value,
            {1, 2, 3, 4, 5},
            TASKS[5].file_id,
            JOBS[0],  # cross validation
            TASKS[5].user_id,
            EXPECTED_DB_VALIDATION_TASKS[0],
        ),
        (
            # this test is for tasks with second job, third file,
            # first user (annotator), second user (validator)
            # validation tasks will be distributed automatically
            AnnotationAndValidationActionsSchema.auto.value,
            {1, 2, 3},
            TASKS[8].file_id,
            JOBS[1],  # hierarchical validation
            TASKS[8].user_id,
            EXPECTED_DB_VALIDATION_TASKS[1],
        ),
        (
            # this test is for tasks with first job, second file,
            # first user (annotator), fourth user (validator)
            # validation tasks should not be created
            AnnotationAndValidationActionsSchema.not_required.value,
            {1, 2, 3, 4, 5},
            TASKS[5].file_id,
            JOBS[0],  # cross validation
            TASKS[5].user_id,
            [],
        ),
        (
            # this test is for tasks with first job, second file,
            # first user (annotator), fourth user (validator)
            # validation tasks should be assigned to specific user
            str(ANNOTATORS[0].user_id),
            {1, 2, 3, 4, 5},
            TASKS[5].file_id,
            JOBS[0],  # cross validation
            TASKS[5].user_id,
            EXPECTED_DB_VALIDATION_TASKS[2],
        ),
        (
            # this test is for tasks with second job, third file,
            # first user (annotator), second user (validator)
            # validation tasks will be assigned to specific user
            str(ANNOTATORS[1].user_id),
            {1, 2, 3},
            TASKS[8].file_id,
            JOBS[1],  # hierarchical validation
            TASKS[8].user_id,
            EXPECTED_DB_VALIDATION_TASKS[1],
        ),
        (
            None,
            {1, 2, 3},
            TASKS[8].file_id,
            JOBS[1],  # hierarchical validation
            TASKS[8].user_id,
            [],
        ),
    ],
)
def test_create_validation_tasks(
    db_validation_end, user, annotated, file_id, job, user_id, expected_tasks
):
    create_validation_tasks(
        validation_user_for_reannotated_pages=user,
        annotated=annotated,
        file_id=file_id,
        job=job,
        user_id=user_id,
        db=db_validation_end,
    )
    db_validation_end.commit()

    tasks = (
        db_validation_end.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.file_id == file_id,
            ManualAnnotationTask.job_id == job.job_id,
            ManualAnnotationTask.status == TaskStatusEnumSchema.ready,
        )
        .all()
    )
    actual_tasks = prepare_result(tasks)

    assert actual_tasks == expected_tasks


@pytest.mark.integration
@pytest.mark.parametrize(
    # second test checks, that there will be exception
    # if user does not belong to job
    ["user_id"],
    [(BAD_UUID,), (str(ANNOTATORS[3].user_id),)],
)
def test_create_annotation_tasks_exceptions(db_validation_end, user_id):
    with pytest.raises(HTTPException):
        create_annotation_tasks(
            annotation_user_for_failed_pages=user_id,
            task_id=1,
            db=db_validation_end,
            failed={1, 2, 3},
            file_id=1,
            job=JOBS[1],
        )


@pytest.mark.integration
@pytest.mark.parametrize(
    ["user"],
    [
        (BAD_UUID,),
        # validator cannot assign himself for his own annotations
        (str(TASKS[4].user_id),),
        # user does not belong to job
        ("90b68bc8-468f-43dc-8981-106b660a8578",),
    ],
)
def test_create_validation_tasks_exceptions(db_validation_end, user):
    with pytest.raises(HTTPException):
        create_validation_tasks(
            validation_user_for_reannotated_pages=user,
            annotated={1, 2, 3},
            file_id=1,
            job=JOBS[0],
            user_id=TASKS[4].user_id,
            db=db_validation_end,
        )


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_id", "validation_info", "expected_status_code", "expected_message"],
    [
        (
            TASKS[4].id,
            {
                "annotation_user_for_failed_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
                "validation_user_for_reannotated_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
            },
            200,
            "",
        ),
        (
            # validator can be assigned for annotation task
            # even if validation type of job is hierarchical
            TASKS[8].id,
            {
                "annotation_user_for_failed_pages": str(ANNOTATORS[1].user_id),
                "validation_user_for_reannotated_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
            },
            200,
            "",
        ),
        (
            TASKS[4].id,
            {
                "annotation_user_for_failed_pages": BAD_UUID,
                "validation_user_for_reannotated_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
            },
            400,
            "Bad UUID",
        ),
        (
            TASKS[4].id,
            {
                "annotation_user_for_failed_pages": str(ANNOTATORS[1].user_id),
                "validation_user_for_reannotated_pages": BAD_UUID,
            },
            400,
            "Bad UUID",
        ),
        (
            # user cannot assign himself for validation of reannotated pages
            # if validation type of job is not hierarchical
            TASKS[4].id,
            {
                "annotation_user_for_failed_pages": str(ANNOTATORS[1].user_id),
                "validation_user_for_reannotated_pages": str(TASKS[4].user_id),
            },
            400,
            "User cannot specify himself",
        ),
        (
            # user can assign himself for validation of reannotated pages
            # if validation type of job is hierarchical
            TASKS[8].id,
            {
                "annotation_user_for_failed_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
                "validation_user_for_reannotated_pages": str(TASKS[8].user_id),
            },
            200,
            "",
        ),
        (
            # if user does not belong to job, task will not be created
            TASKS[8].id,
            {
                "annotation_user_for_failed_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
                "validation_user_for_reannotated_pages": str(
                    ANNOTATORS[3].user_id
                ),
            },
            400,
            "does not belong",
        ),
        (
            # if user does not belong to job, task will not be created
            TASKS[8].id,
            {
                "annotation_user_for_failed_pages": str(ANNOTATORS[3].user_id),
                "validation_user_for_reannotated_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
            },
            400,
            "does not belong",
        ),
        (
            # only owner may not request validation of edited pages
            # user of this task is not owner
            TASKS[4].id,
            {
                "annotation_user_for_failed_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
                "validation_user_for_reannotated_pages": AnnotationAndValidationActionsSchema.not_required.value,  # noqa E501
            },
            400,
            "Only owner may",
        ),
        (
            # only owner may not request validation of edited pages
            # user of this task is owner
            TASKS[5].id,
            {
                "annotation_user_for_failed_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
                "validation_user_for_reannotated_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
            },
            200,
            "",
        ),
        (
            # validator cannot finish task,
            # if there are unprocessed pages
            TASKS[9].id,
            {},
            400,
            "Cannot finish validation task",
        ),
        (
            # when finishing task for annotation
            # there should not be values for edited and failed pages
            # but None is acceptable
            TASKS[10].id,
            {
                "validation_user_for_reannotated_pages": AnnotationAndValidationActionsSchema.not_required.value  # noqa E501
            },
            400,
            "This task is for annotation",
        ),
        (
            TASKS[4].id,
            {
                "validation_user_for_reannotated_pages": str(
                    ANNOTATORS[1].user_id
                )
            },
            400,
            "Missing `annotation_user",
        ),
        (
            TASKS[5].id,
            {
                "annotation_user_for_failed_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
            },
            400,
            "Missing `validation_user",
        ),
        (
            TASKS[5].id,
            None,
            400,
            "Missing `annotation_user",
        ),
        (
            TASKS[5].id,
            {},
            400,
            "Missing `annotation_user",
        ),
        # in this validation task (TASKS[6]) every page is marked
        # as validated,
        # thus annotation_user_for_failed_pages param is excessive
        (
            TASKS[6].id,
            {
                "annotation_user_for_failed_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
            },
            400,
            "Validator did not mark any pages as failed",
        ),
        # in this validation task (TASKS[12]) every page is edited,
        # thus annotation_user_for_failed_pages param is excessive
        (
            TASKS[12].id,
            {
                "annotation_user_for_failed_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
                "validation_user_for_reannotated_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
            },
            400,
            "Validator did not mark any pages as failed",
        ),
        # in this validation task (TASKS[13]) every page
        # is marked as failed,
        # thus validation_user_for_reannotated_pages param is excessive
        (
            TASKS[13].id,
            {
                "annotation_user_for_failed_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
                "validation_user_for_reannotated_pages": AnnotationAndValidationActionsSchema.auto.value,  # noqa E501
            },
            400,
            "Validator did not edit any pages",
        ),
    ],
)
def test_finish_task_status_codes(
    db_validation_end,
    task_id,
    validation_info,
    expected_status_code,
    expected_message,
):
    """
    Note, that there is not mocked requests to jobs service.
    They are not happening, because either all previous tasks
    were done, but new tasks were created and job cannot be finished
    or not all previous tasks were finished.
    """
    response = client.post(
        FINISH_TASK_PATH.format(task_id=task_id),
        headers=TEST_HEADERS,
        json=validation_info,
    )

    check_files_distributed_pages(db_validation_end, TASKS[4].job_id)
    check_files_finished_pages(db_validation_end, TASKS[4].job_id, TEST_TENANT)
    assert response.status_code == expected_status_code
    assert expected_message in response.text


@pytest.mark.integration
def test_finish_task_successful_status_codes(
    db_validation_end,
):
    """
    Validator in these revisions edited and marked
    as validated page 4, which means there is no need for
    validation of his annotations.
    Validator in these revisions edited and marked
    as failed page 1, which means, that validation
    task for his annotation will be created.
    Task for annotation for page 1 will not be created.
    """
    expected_db_tasks = [
        {
            "file_id": TASKS[4].file_id,
            "pages": [2, 3],
            "job_id": TASKS[5].job_id,
            "user_id": str(ANNOTATORS[0].user_id),
            "is_validation": False,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[4].file_id,
            "pages": [2],
            "job_id": TASKS[5].job_id,
            "user_id": str(ANNOTATORS[1].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[4].file_id,
            "pages": [3],
            "job_id": TASKS[5].job_id,
            "user_id": str(ANNOTATORS[3].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.pending,
            "deadline": JOBS[0].deadline,
        },
        {
            "file_id": TASKS[4].file_id,
            "pages": [1],
            "job_id": TASKS[4].job_id,
            "user_id": str(ANNOTATORS[0].user_id),
            "is_validation": True,
            "status": TaskStatusEnumSchema.ready,
            "deadline": JOBS[0].deadline,
        },
    ]
    task_id = TASKS[4].id
    validation_info = {
        # failed: [2, 3]
        "annotation_user_for_failed_pages": str(ANNOTATORS[0].user_id),
        # edited: [1]
        "validation_user_for_reannotated_pages": str(
            ANNOTATORS[0].user_id
        ),  # noqa E501
    }

    response = client.post(
        FINISH_TASK_PATH.format(task_id=task_id),
        headers=TEST_HEADERS,
        json=validation_info,
    )
    tasks = (
        db_validation_end.query(ManualAnnotationTask)
        .filter(
            or_(
                ManualAnnotationTask.status == TaskStatusEnumSchema.pending,
                ManualAnnotationTask.status == TaskStatusEnumSchema.ready,
            ),
        )
        .all()
    )
    actual_tasks = prepare_result(tasks)

    check_files_distributed_pages(db_validation_end, TASKS[4].job_id)
    check_files_finished_pages(db_validation_end, TASKS[4].job_id, TEST_TENANT)
    assert response.status_code == 200
    assert actual_tasks == expected_db_tasks


@pytest.mark.integration
def test_check_delete_user_from_annotated_doc(db_validation_end):
    # check that a user is in DB
    annotator_to_delete = db_validation_end.query(
        db_validation_end.query(User)
        .filter(User.user_id == ANNOTATORS[0].user_id)
        .exists()
    ).scalar()
    assert annotator_to_delete is True
    # delete user`s tasks because without it a user can`t be deleted
    db_validation_end.query(ManualAnnotationTask).filter(
        ManualAnnotationTask.id.in_([100, 102, 103, 107, 111])
    ).delete(synchronize_session=False)
    db_validation_end.commit()
    db_validation_end.query(User).filter(
        User.user_id == ANNOTATORS[0].user_id
    ).delete()
    db_validation_end.commit()

    deleted_user = db_validation_end.query(
        db_validation_end.query(User)
        .filter(User.user_id == ANNOTATORS[0].user_id)
        .exists()
    ).scalar()
    assert not deleted_user
    revision = (
        db_validation_end.query(AnnotatedDoc)
        .filter(AnnotatedDoc.revision == "2")
        .first()
    )
    assert not revision.user
