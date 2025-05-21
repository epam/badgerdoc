from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.sql import not_

from annotation.annotations import row_to_dict
from annotation.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from annotation.models import File, Job, ManualAnnotationTask, User
from annotation.schemas import (
    FileStatusEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from tests.override_app_dependency import (
    TEST_HEADERS,
    TEST_TENANT,
    TEST_TOKEN,
    app,
)
from tests.test_post import check_files_distributed_pages

client = TestClient(app)

POST_TASKS_FOR_UNASSIGNED_FILES_PATH = "/distribution/{job_id}"
ANNOTATORS_POST_UN_FILES = [
    User(user_id="10b68bc8-468f-43dc-8981-106b660a8578"),
    User(user_id="20b68bc8-468f-43dc-8981-106b660a8578"),
]
JOBS = [
    Job(
        job_id=1,
        callback_url="http://www.test.com",
        annotators=[
            ANNOTATORS_POST_UN_FILES[0],
            ANNOTATORS_POST_UN_FILES[1],
        ],
        is_auto_distribution=False,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
        validation_type=ValidationSchema.cross,
    ),
    Job(
        job_id=2,
        callback_url="http://www.test.com",
        annotators=[
            ANNOTATORS_POST_UN_FILES[0],
        ],
        is_auto_distribution=False,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
        validation_type=ValidationSchema.cross,
    ),
]
FILES = [
    File(
        file_id=1,
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=5,
        distributed_annotating_pages=[1, 2, 3, 4, 5],
        annotated_pages=[],
        distributed_validating_pages=[1, 2, 3, 4, 5],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),  # file was fully distributed
    File(
        file_id=2,
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=5,
        distributed_annotating_pages=[],
        annotated_pages=[],
        distributed_validating_pages=[],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),  # file was not distributed at all
    File(
        file_id=3,
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=5,
        distributed_annotating_pages=[1, 4, 1],
        annotated_pages=[],
        distributed_validating_pages=[1, 4],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),  # file was partially distributed
    File(
        file_id=4,
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=6,
        distributed_annotating_pages=[1, 4],
        annotated_pages=[],
        distributed_validating_pages=[2, 4],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),  # file was partially distributed
]
TASKS = [
    ManualAnnotationTask(
        file_id=FILES[0].file_id,
        pages=[1, 2, 3, 4, 5],
        job_id=FILES[0].job_id,
        user_id=ANNOTATORS_POST_UN_FILES[0].user_id,
        is_validation=True,
        deadline=JOBS[0].deadline,
        status=TaskStatusEnumSchema.in_progress,
    ),
    ManualAnnotationTask(
        file_id=FILES[0].file_id,
        pages=[1, 2, 3, 4, 5],
        job_id=FILES[0].job_id,
        user_id=ANNOTATORS_POST_UN_FILES[0].user_id,
        is_validation=False,
        deadline=JOBS[0].deadline,
        status=TaskStatusEnumSchema.in_progress,
    ),
    ManualAnnotationTask(
        file_id=FILES[2].file_id,
        pages=[1, 4],
        job_id=FILES[2].job_id,
        user_id=ANNOTATORS_POST_UN_FILES[0].user_id,
        is_validation=True,
        deadline=JOBS[0].deadline,
        status=TaskStatusEnumSchema.in_progress,
    ),
    ManualAnnotationTask(
        file_id=FILES[2].file_id,
        pages=[1, 4, 1],
        job_id=FILES[2].job_id,
        user_id=ANNOTATORS_POST_UN_FILES[0].user_id,
        is_validation=False,
        deadline=JOBS[0].deadline,
        status=TaskStatusEnumSchema.in_progress,
    ),
    ManualAnnotationTask(
        file_id=FILES[3].file_id,
        pages=[2, 4],
        job_id=FILES[3].job_id,
        user_id=ANNOTATORS_POST_UN_FILES[0].user_id,
        is_validation=True,
        deadline=JOBS[0].deadline,
        status=TaskStatusEnumSchema.in_progress,
    ),
    ManualAnnotationTask(
        file_id=FILES[3].file_id,
        pages=[1, 4],
        job_id=FILES[3].job_id,
        user_id=ANNOTATORS_POST_UN_FILES[0].user_id,
        is_validation=False,
        deadline=JOBS[0].deadline,
        status=TaskStatusEnumSchema.in_progress,
    ),
]
JOBS_FILES_TASKS_POST_UN_FILES = JOBS + FILES + TASKS

EXPECTED_FILES = [
    dict(
        file_id=1,
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=5,
        distributed_annotating_pages=[1, 2, 3, 4, 5],
        annotated_pages=[],
        distributed_validating_pages=[1, 2, 3, 4, 5],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),
    dict(
        file_id=2,
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=5,
        distributed_annotating_pages=[1, 2, 3, 4, 5],
        annotated_pages=[],
        distributed_validating_pages=[1, 2, 3, 4, 5],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),
    dict(
        file_id=3,
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=5,
        distributed_annotating_pages=[1, 2, 3, 4, 5],
        annotated_pages=[],
        distributed_validating_pages=[1, 2, 3, 4, 5],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),
    dict(
        file_id=4,
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=6,
        distributed_annotating_pages=[1, 2, 3, 4, 5, 6],
        annotated_pages=[],
        distributed_validating_pages=[1, 2, 3, 4, 5, 6],
        validated_pages=[],
        status=FileStatusEnumSchema.pending,
    ),
]

EXPECTED_TASKS = [
    {
        "deadline": JOBS[0].deadline,
        "file_id": FILES[1].file_id,
        "is_validation": False,
        "job_id": FILES[1].job_id,
        "pages": [1, 2, 3, 4, 5],
        "status": TaskStatusEnumSchema.pending,
        "user_id": ANNOTATORS_POST_UN_FILES[1].user_id,
    },
    {
        "deadline": JOBS[0].deadline,
        "file_id": FILES[3].file_id,
        "is_validation": False,
        "job_id": FILES[1].job_id,
        "pages": [2, 3, 5, 6],
        "status": TaskStatusEnumSchema.pending,
        "user_id": ANNOTATORS_POST_UN_FILES[1].user_id,
    },
    {
        "deadline": JOBS[0].deadline,
        "file_id": FILES[2].file_id,
        "is_validation": False,
        "job_id": FILES[1].job_id,
        "pages": [2, 3, 5],
        "status": TaskStatusEnumSchema.pending,
        "user_id": ANNOTATORS_POST_UN_FILES[0].user_id,
    },
    {
        "deadline": JOBS[0].deadline,
        "file_id": FILES[2].file_id,
        "is_validation": True,
        "job_id": FILES[1].job_id,
        "pages": [2, 3, 5],
        "status": TaskStatusEnumSchema.pending,
        "user_id": ANNOTATORS_POST_UN_FILES[1].user_id,
    },
    {
        "deadline": JOBS[0].deadline,
        "file_id": FILES[1].file_id,
        "is_validation": True,
        "job_id": FILES[1].job_id,
        "pages": [1, 2, 3, 4, 5],
        "status": TaskStatusEnumSchema.pending,
        "user_id": ANNOTATORS_POST_UN_FILES[0].user_id,
    },
    {
        "deadline": JOBS[0].deadline,
        "file_id": FILES[3].file_id,
        "is_validation": True,
        "job_id": FILES[1].job_id,
        "pages": [1],
        "status": TaskStatusEnumSchema.pending,
        "user_id": ANNOTATORS_POST_UN_FILES[1].user_id,
    },
    {
        "deadline": JOBS[0].deadline,
        "file_id": FILES[3].file_id,
        "is_validation": True,
        "job_id": FILES[1].job_id,
        "pages": [3, 5, 6],
        "status": TaskStatusEnumSchema.pending,
        "user_id": ANNOTATORS_POST_UN_FILES[0].user_id,
    },
]


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_id", "tenant", "expected_code", "expected_message"],
    [
        (10, TEST_TENANT, 400, "wrong job_id"),
        ("abc", TEST_TENANT, 422, "value is not a valid integer"),
        (10, "bad-tenant", 400, "wrong job_id"),
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_post_tasks_for_unassigned_files_error_status_codes(
    db_post_unassigned_files,
    job_id,
    tenant,
    expected_code,
    expected_message,
):
    response = client.post(
        POST_TASKS_FOR_UNASSIGNED_FILES_PATH.format(job_id=job_id),
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )

    assert response.status_code == expected_code
    assert expected_message in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_id", "expected_tasks", "expected_files"],
    [
        (JOBS[0].job_id, EXPECTED_TASKS, EXPECTED_FILES),
        (JOBS[1].job_id, [], []),
    ],
)
@patch("annotation.distribution.main.SPLIT_MULTIPAGE_DOC", "true")
@pytest.mark.skip(reason="tests refactoring")
def test_post_tasks_for_unassigned_files(
    db_post_unassigned_files, job_id, expected_tasks, expected_files
):
    first_response = client.post(
        POST_TASKS_FOR_UNASSIGNED_FILES_PATH.format(job_id=job_id),
        headers=TEST_HEADERS,
    )  # if there is something to distribute, this response won`t be empty
    check_files_distributed_pages(db_post_unassigned_files, job_id)

    second_response = client.post(
        POST_TASKS_FOR_UNASSIGNED_FILES_PATH.format(job_id=job_id),
        headers=TEST_HEADERS,
    )  # second response for same job should be empty
    check_files_distributed_pages(db_post_unassigned_files, job_id)

    tasks_in_db = (
        db_post_unassigned_files.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.job_id == job_id,
            not_(
                ManualAnnotationTask.status == TaskStatusEnumSchema.in_progress
            ),
        )
        .all()
    )
    tasks_in_db = [row_to_dict(task) for task in tasks_in_db]
    for task_in_db in tasks_in_db:
        del task_in_db["id"]

    actual_response = first_response.json()
    for task in actual_response:
        del task["id"]

    files_in_db = (
        db_post_unassigned_files.query(File)
        .filter(File.job_id == job_id)
        .all()
    )
    files_in_db = [row_to_dict(f) for f in files_in_db]

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    # check, if distribution belongs to one of the variations

    assert tasks_in_db == expected_tasks
    assert files_in_db == expected_files
    # check, if distribution belongs to one of the variations
    assert actual_response == expected_tasks


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["db_errors"],
    [
        (DBAPIError,),
        (SQLAlchemyError,),
    ],
    indirect=["db_errors"],
)
def test_post_tasks_for_unassigned_files_db_exceptions(monkeypatch, db_errors):
    response = client.post(
        POST_TASKS_FOR_UNASSIGNED_FILES_PATH.format(job_id=JOBS[0].job_id),
        headers=TEST_HEADERS,
    )
    assert response.status_code == 500
