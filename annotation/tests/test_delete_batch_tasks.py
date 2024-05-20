from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from tests.consts import CRUD_TASKS_PATH
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app
from tests.test_post import check_files_distributed_pages
from tests.test_tasks_crud_ud import BAD_ID, NOT_EXISTING_ID

from annotation.annotations import row_to_dict
from annotation.models import Category, File, Job, ManualAnnotationTask, User
from annotation.schemas import (
    CategoryTypeSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)

client = TestClient(app)

DELETE_BATCH_TASKS_ANNOTATOR = User(
    user_id="18d3d189-e73a-4680-bfa7-7ba3fe6ebee5"
)
CATEGORIES = [
    Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    )
]
VALIDATION_TYPE = "cross"
TASK = {
    "id": 1,
    "file_id": 1,
    "pages": [1],
    "job_id": 1,
    "user_id": "18d3d189-e73a-4680-bfa7-7ba3fe6ebee5",
    "is_validation": True,
    "status": "Pending",
    "deadline": None,
}

DELETE_BATCH_TASKS_FILE = File(
    **{
        "file_id": 1,
        "tenant": TEST_TENANT,
        "job_id": TASK["job_id"],
        "pages_number": 10,
        "distributed_validating_pages": [1],
    }
)

DELETE_BATCH_TASKS_JOB = Job(
    **{
        "job_id": TASK["job_id"],
        "callback_url": "http://www.test.com",
        "annotators": [DELETE_BATCH_TASKS_ANNOTATOR],
        "validation_type": ValidationSchema.cross,
        "files": [DELETE_BATCH_TASKS_FILE],
        "is_auto_distribution": False,
        "categories": CATEGORIES,
        "deadline": None,
        "tenant": TEST_TENANT,
    }
)

TASK_PENDING = deepcopy(TASK)
TASK_PENDING["id"] = 1
TASK_PENDING["status"] = TaskStatusEnumSchema.pending

TASK_READY = deepcopy(TASK)
TASK_READY["id"] = 2
TASK_READY["status"] = TaskStatusEnumSchema.ready

TASK_IN_PROGRESS = deepcopy(TASK)
TASK_IN_PROGRESS["id"] = 3
TASK_IN_PROGRESS["status"] = TaskStatusEnumSchema.in_progress

TASK_FINISHED = deepcopy(TASK)
TASK_FINISHED["id"] = 4
TASK_FINISHED["status"] = TaskStatusEnumSchema.finished

DIFF_STATUSES_TASKS = [
    TASK_PENDING,
    TASK_READY,
    TASK_IN_PROGRESS,
    TASK_FINISHED,
]

PENDING_READY_IDS = [TASK_PENDING["id"], TASK_READY["id"]]


@pytest.mark.integration
@pytest.mark.parametrize(
    ["tasks_id", "job_id", "expected_code"],
    [
        (PENDING_READY_IDS, TASK["job_id"], 204),  # tasks are in db and
        # their statuses are acceptable for delete
        (
            [TASK_PENDING["id"], TASK_IN_PROGRESS["id"], TASK_FINISHED["id"]],
            TASK["job_id"],
            400,
        ),  # tasks are in db, but
        # not all statuses are acceptable for delete
        (
            [TASK_IN_PROGRESS["id"], TASK_FINISHED["id"]],
            TASK["job_id"],
            400,
        ),  # tasks are in db, but
        # no statuses are acceptable for delete
        (
            [NOT_EXISTING_ID, TASK_FINISHED["id"]],
            TASK["job_id"],
            400,
        ),  # not all tasks are in db and
        # no statuses are acceptable for delete
        (
            [TASK_PENDING["id"], NOT_EXISTING_ID],
            TASK["job_id"],
            400,
        ),  # not all tasks are in db
        ([BAD_ID], TASK["job_id"], 422),
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_delete_batch_tasks_status_codes(
    prepare_db_for_batch_delete_tasks, tasks_id, job_id, expected_code
):
    response = client.delete(
        CRUD_TASKS_PATH, json=tasks_id, headers=TEST_HEADERS
    )
    assert response.status_code == expected_code
    check_files_distributed_pages(prepare_db_for_batch_delete_tasks, job_id)


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["db_errors"],
    [
        (DBAPIError,),
        (SQLAlchemyError,),
    ],
    indirect=["db_errors"],
)
def test_delete_batch_tasks_exceptions(
    monkeypatch,
    db_errors,
):
    response = client.delete(
        CRUD_TASKS_PATH, json=[TASK_PENDING["id"]], headers=TEST_HEADERS
    )
    assert response.status_code == 500


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "tasks_id",
        "job_id",
        "tasks_before_removing",
        "expected_response",
        "expected_tasks_in_db",
    ],
    [
        (PENDING_READY_IDS, TASK["job_id"], DIFF_STATUSES_TASKS[:2], b"", []),
        (
            [TASK_READY["id"], TASK_IN_PROGRESS["id"]],
            TASK["job_id"],
            DIFF_STATUSES_TASKS[1:3],
            {
                "detail": "Error: task(s) from given list "
                "were not found or their status does not "
                f"match with [{TaskStatusEnumSchema.pending}] "
                f"or [{TaskStatusEnumSchema.ready}]."
            },
            DIFF_STATUSES_TASKS[1:3],
        ),
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_delete_task(
    prepare_db_for_batch_delete_tasks,
    tasks_id,
    job_id,
    tasks_before_removing,
    expected_response,
    expected_tasks_in_db,
):
    tasks = (
        prepare_db_for_batch_delete_tasks.query(ManualAnnotationTask)
        .filter(ManualAnnotationTask.id.in_(tasks_id))
        .all()
    )

    tasks = [row_to_dict(task) for task in tasks]

    assert tasks == tasks_before_removing

    if expected_response:
        response = client.delete(
            CRUD_TASKS_PATH, json=tasks_id, headers=TEST_HEADERS
        ).json()
    else:
        response = client.delete(
            CRUD_TASKS_PATH, json=tasks_id, headers=TEST_HEADERS
        ).content

    tasks = (
        prepare_db_for_batch_delete_tasks.query(ManualAnnotationTask)
        .filter(ManualAnnotationTask.id.in_(tasks_id))
        .all()
    )
    tasks = [row_to_dict(task) for task in tasks]
    assert response == expected_response
    assert tasks == expected_tasks_in_db
    check_files_distributed_pages(prepare_db_for_batch_delete_tasks, job_id)
