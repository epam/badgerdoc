import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from tests.consts import CRUD_TASKS_PATH
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app
from tests.test_post import check_files_distributed_pages

from annotation.annotations import row_to_dict
from annotation.models import Category, File, Job, ManualAnnotationTask, User
from annotation.schemas import (
    CategoryTypeSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)

client = TestClient(app)

CRUD_UD_USER = User(user_id="1a8b0bd3-9159-4078-a60a-1d652b61c944")
CRUD_UD_FILE_1 = File(
    **{
        "file_id": 1,
        "tenant": TEST_TENANT,
        "job_id": 1,
        "pages_number": 10,
        "distributed_annotating_pages": [],
        "distributed_validating_pages": [1],
    }
)
CRUD_UD_FILE_2 = File(
    **{
        "file_id": 2,
        "tenant": TEST_TENANT,
        "job_id": 2,
        "pages_number": 10,
    }
)
CATEGORIES = [
    Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    ),
]
CRUD_UD_JOB_1 = Job(
    **{
        "job_id": 1,
        "callback_url": "http://www.test.com/test1",
        "annotators": [CRUD_UD_USER],
        "validation_type": ValidationSchema.cross,
        "files": [CRUD_UD_FILE_1],
        "is_auto_distribution": False,
        "categories": CATEGORIES,
        "deadline": None,
        "tenant": TEST_TENANT,
    }
)
CRUD_UD_JOB_2 = Job(
    **{
        "job_id": 2,
        "callback_url": "http://www.test.com/test1",
        "annotators": [CRUD_UD_USER],
        "validation_type": ValidationSchema.cross,
        "files": [CRUD_UD_FILE_2],
        "is_auto_distribution": False,
        "categories": CATEGORIES,
        "deadline": "2021-10-19T01:01:01",
        "tenant": TEST_TENANT,
    }
)
CRUD_UD_CONSTRAINTS_USERS = [
    User(user_id="1a8b0bd3-9159-4078-a60a-1d652b61c911"),
    User(user_id="1a8b0bd3-9159-4078-a60a-1d652b61c912"),
    User(user_id="1a8b0bd3-9159-4078-a60a-1d652b61c913"),
]

CRUD_UD_CONSTRAINTS_FILES = [
    File(file_id=10, tenant=TEST_TENANT, job_id=10, pages_number=3),
    File(file_id=10, tenant=TEST_TENANT, job_id=11, pages_number=6),
    File(file_id=10, tenant=TEST_TENANT, job_id=12, pages_number=7),
    File(file_id=11, tenant=TEST_TENANT, job_id=10, pages_number=8),
    File(file_id=13, tenant=TEST_TENANT, job_id=13, pages_number=1),
    File(file_id=11, tenant=TEST_TENANT, job_id=11, pages_number=2),
]

CRUD_UD_CONSTRAINTS_JOBS = [
    Job(
        job_id=10,
        callback_url="http://www.test.com/test1",
        annotators=CRUD_UD_CONSTRAINTS_USERS[:2],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=11,
        callback_url="http://www.test.com/test1",
        annotators=CRUD_UD_CONSTRAINTS_USERS[:2],
        validators=CRUD_UD_CONSTRAINTS_USERS[1:],
        validation_type=ValidationSchema.hierarchical,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=12,
        callback_url="http://www.test.com/test1",
        validators=[CRUD_UD_CONSTRAINTS_USERS[2]],
        validation_type=ValidationSchema.validation_only,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=13,
        callback_url="http://www.test.com/test1",
        annotators=CRUD_UD_CONSTRAINTS_USERS,
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=TEST_TENANT,
    ),
]

CRUD_UD_CONSTRAINTS_TASKS = [
    ManualAnnotationTask(
        id=1,
        file_id=CRUD_UD_CONSTRAINTS_FILES[3].file_id,
        pages=list(range(1, 5)),
        job_id=CRUD_UD_CONSTRAINTS_JOBS[0].job_id,
        user_id=CRUD_UD_CONSTRAINTS_USERS[0].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.pending,
        deadline="2021-10-19T01:01:01",
    ),
    ManualAnnotationTask(
        id=2,
        file_id=CRUD_UD_CONSTRAINTS_FILES[1].file_id,
        pages=[1, 2, 3],
        job_id=CRUD_UD_CONSTRAINTS_JOBS[0].job_id,
        user_id=CRUD_UD_CONSTRAINTS_USERS[0].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.pending,
        deadline="2021-10-19T01:01:01",
    ),
    ManualAnnotationTask(
        id=3,
        file_id=CRUD_UD_CONSTRAINTS_FILES[1].file_id,
        pages=[1, 2, 3],
        job_id=CRUD_UD_CONSTRAINTS_JOBS[0].job_id,
        user_id=CRUD_UD_CONSTRAINTS_USERS[0].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.pending,
        deadline="2021-10-19T01:01:01",
    ),
    ManualAnnotationTask(
        id=4,
        file_id=CRUD_UD_CONSTRAINTS_FILES[3].file_id,
        pages=list(range(1, 5)),
        job_id=CRUD_UD_CONSTRAINTS_JOBS[0].job_id,
        user_id=CRUD_UD_CONSTRAINTS_USERS[0].user_id,
        is_validation=True,
        status=TaskStatusEnumSchema.ready,
    ),
    ManualAnnotationTask(
        id=5,
        file_id=CRUD_UD_CONSTRAINTS_FILES[3].file_id,
        pages=list(range(1, 5)),
        job_id=CRUD_UD_CONSTRAINTS_JOBS[0].job_id,
        user_id=CRUD_UD_CONSTRAINTS_USERS[0].user_id,
        is_validation=True,
        status=TaskStatusEnumSchema.in_progress,
    ),
    ManualAnnotationTask(
        id=6,
        file_id=CRUD_UD_CONSTRAINTS_FILES[3].file_id,
        pages=list(range(1, 5)),
        job_id=CRUD_UD_CONSTRAINTS_JOBS[0].job_id,
        user_id=CRUD_UD_CONSTRAINTS_USERS[0].user_id,
        is_validation=True,
        status=TaskStatusEnumSchema.finished,
    ),
    ManualAnnotationTask(
        id=7,
        file_id=CRUD_UD_CONSTRAINTS_FILES[1].file_id,
        pages=[1, 2, 3],
        job_id=CRUD_UD_CONSTRAINTS_JOBS[1].job_id,
        user_id=CRUD_UD_CONSTRAINTS_USERS[2].user_id,
        is_validation=True,
        status=TaskStatusEnumSchema.pending,
    ),
    ManualAnnotationTask(
        id=8,
        file_id=CRUD_UD_CONSTRAINTS_FILES[2].file_id,
        pages=[1, 2, 3],
        job_id=CRUD_UD_CONSTRAINTS_JOBS[2].job_id,
        user_id=CRUD_UD_CONSTRAINTS_USERS[2].user_id,
        is_validation=True,
        status=TaskStatusEnumSchema.pending,
    ),
    ManualAnnotationTask(
        id=9,
        file_id=CRUD_UD_CONSTRAINTS_FILES[4].file_id,
        pages=[1],
        job_id=CRUD_UD_CONSTRAINTS_JOBS[3].job_id,
        user_id=CRUD_UD_CONSTRAINTS_USERS[0].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.pending,
    ),
]

CRUD_UD_TASK = {
    "id": 1,
    "file_id": CRUD_UD_FILE_1.file_id,
    "pages": [1],
    "job_id": CRUD_UD_JOB_1.job_id,
    "user_id": CRUD_UD_USER.user_id,
    "is_validation": True,
    "status": TaskStatusEnumSchema.pending,
    "deadline": None,
}
CRUD_UD_UPDATED_TASK = {
    "id": CRUD_UD_TASK["id"],
    "file_id": CRUD_UD_FILE_2.file_id,
    "pages": [1, 2],
    "job_id": CRUD_UD_JOB_2.job_id,
    "user_id": CRUD_UD_USER.user_id,
    "is_validation": False,
    "status": TaskStatusEnumSchema.pending,
    "deadline": "2021-10-19T01:01:01",
}
EMPTY_UD_TASK = {
    "id": CRUD_UD_TASK["id"],
    "file_id": None,
    "job_id": None,
    "pages": None,
    "user_id": None,
    "is_validation": None,
    "status": TaskStatusEnumSchema.in_progress,
    "deadline": None,
}
CRUD_UD_TASK_ID = CRUD_UD_TASK["id"]
NOT_EXISTING_USER_ID = "e0433fc7-97f1-47ab-af5e-248210b32c4e"

UPDATE_QUERY = {
    "file_id": CRUD_UD_FILE_2.file_id,
    "user_id": CRUD_UD_USER.user_id,
    "pages": [1, 2, 1],
    "job_id": CRUD_UD_FILE_2.job_id,
    "is_validation": False,
    "deadline": "2021-10-19T01:01:01",
}
TASK_TO_UPDATE = {
    key: value
    for key, value in EMPTY_UD_TASK.items()
    for key, value in UPDATE_QUERY.items()
    if value is not None
}

NOT_EXISTING_ID = 5
NOT_EXIST_JOB_ID = 1000
NOT_EXISTING_FILE_ID = 1000
BAD_ID = "bad_id"

PG_TASK = ManualAnnotationTask(**CRUD_UD_TASK)


def construct_path(path, task_id):
    return path + f"/{task_id}"


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_id", "old_job_id", "new_job_id", "request_body", "expected_code"],
    [
        (
            CRUD_UD_TASK_ID,
            CRUD_UD_TASK["job_id"],
            CRUD_UD_TASK["job_id"],
            CRUD_UD_TASK,
            200,
        ),
        (
            CRUD_UD_TASK_ID,
            CRUD_UD_TASK["job_id"],
            CRUD_UD_TASK["job_id"],
            CRUD_UD_UPDATED_TASK,
            200,
        ),
        (
            CRUD_UD_TASK_ID,
            CRUD_UD_TASK["job_id"],
            CRUD_UD_TASK["job_id"],
            {},
            200,
        ),
        (
            CRUD_UD_TASK_ID,
            CRUD_UD_TASK["job_id"],
            CRUD_UD_TASK["job_id"],
            {"job_id": NOT_EXIST_JOB_ID},
            400,
        ),
        (
            NOT_EXISTING_ID,
            CRUD_UD_TASK["job_id"],
            CRUD_UD_TASK["job_id"],
            EMPTY_UD_TASK,
            404,
        ),
        (
            CRUD_UD_TASK_ID,
            CRUD_UD_TASK["job_id"],
            CRUD_UD_TASK["job_id"],
            {"user_id": NOT_EXISTING_USER_ID},
            400,
        ),
        (BAD_ID, CRUD_UD_TASK["job_id"], CRUD_UD_TASK["job_id"], {}, 422),
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_update_task_status_codes(
    prepare_db_for_ud_task,
    task_id,
    old_job_id,
    new_job_id,
    request_body,
    expected_code,
):
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, task_id),
        json=request_body,
        headers=TEST_HEADERS,
    )
    assert response.status_code == expected_code
    check_files_distributed_pages(prepare_db_for_ud_task, old_job_id)
    check_files_distributed_pages(prepare_db_for_ud_task, new_job_id)


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["db_errors"],
    [
        (DBAPIError,),
        (SQLAlchemyError,),
    ],
    indirect=["db_errors"],
)
def test_update_task_exceptions(monkeypatch, db_errors):
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, CRUD_UD_TASK_ID),
        headers=TEST_HEADERS,
        json=EMPTY_UD_TASK,
    )
    assert response.status_code == 500


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "task_id",
        "old_job_id",
        "new_job_id",
        "request_body",
        "expected_response",
        "expected_task_in_db",
    ],
    [
        (
            CRUD_UD_TASK_ID,
            CRUD_UD_TASK["job_id"],
            CRUD_UD_TASK["job_id"],
            CRUD_UD_TASK,
            CRUD_UD_TASK,
            CRUD_UD_TASK,
        ),
        (
            CRUD_UD_TASK_ID,
            CRUD_UD_TASK["job_id"],
            CRUD_UD_JOB_2.job_id,
            TASK_TO_UPDATE,
            CRUD_UD_UPDATED_TASK,
            CRUD_UD_UPDATED_TASK,
        ),
        (
            NOT_EXISTING_ID,
            CRUD_UD_TASK["job_id"],
            CRUD_UD_TASK["job_id"],
            EMPTY_UD_TASK,
            "found.",
            None,
        ),
        (
            CRUD_UD_TASK_ID,
            CRUD_UD_TASK["job_id"],
            CRUD_UD_TASK["job_id"],
            {"user_id": NOT_EXISTING_USER_ID},
            f"is not assigned as validator for job {CRUD_UD_TASK['job_id']}",
            CRUD_UD_TASK,
        ),
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_update_task(
    prepare_db_for_ud_task,
    task_id,
    old_job_id,
    new_job_id,
    request_body,
    expected_response,
    expected_task_in_db,
):
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, task_id),
        json=request_body,
        headers=TEST_HEADERS,
    ).json()
    task = (
        prepare_db_for_ud_task.query(ManualAnnotationTask)
        .filter(ManualAnnotationTask.id == task_id)
        .first()
    )
    if task:
        actual_result = row_to_dict(task)
    else:
        actual_result = task
    if response and "detail" in response:
        assert expected_response in response["detail"]
    else:
        assert response == expected_response
    assert actual_result == expected_task_in_db
    check_files_distributed_pages(prepare_db_for_ud_task, old_job_id)
    check_files_distributed_pages(prepare_db_for_ud_task, new_job_id)


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_id", "job_id", "expected_code"],
    [
        (CRUD_UD_TASK_ID, CRUD_UD_JOB_1.job_id, 204),
        (NOT_EXISTING_ID, CRUD_UD_JOB_1.job_id, 404),
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_delete_task_status_codes(
    prepare_db_for_ud_task, task_id, job_id, expected_code
):
    response = client.delete(
        construct_path(CRUD_TASKS_PATH, task_id), headers=TEST_HEADERS
    )
    assert response.status_code == expected_code
    check_files_distributed_pages(prepare_db_for_ud_task, job_id)


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["db_errors"],
    [
        (DBAPIError,),
        (SQLAlchemyError,),
    ],
    indirect=["db_errors"],
)
def test_delete_task_exceptions(monkeypatch, db_errors):
    response = client.delete(
        construct_path(CRUD_TASKS_PATH, CRUD_UD_TASK_ID),
        headers=TEST_HEADERS,
        json=EMPTY_UD_TASK,
    )
    assert response.status_code == 500


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "task_id",
        "job_id",
        "task_before_removing",
        "expected_response",
        "expected_task_in_db",
    ],
    [
        (CRUD_UD_TASK_ID, CRUD_UD_JOB_1.job_id, CRUD_UD_TASK, b"", None),
        (
            NOT_EXISTING_ID,
            CRUD_UD_JOB_1.job_id,
            None,
            {"detail": f"Task with id [{NOT_EXISTING_ID}] was not found."},
            None,
        ),
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_delete_task(
    prepare_db_for_ud_task,
    task_id,
    job_id,
    task_before_removing,
    expected_response,
    expected_task_in_db,
):
    task = (
        prepare_db_for_ud_task.query(ManualAnnotationTask)
        .filter(ManualAnnotationTask.id == task_id)
        .first()
    )
    if task:
        task = row_to_dict(task)

    assert task == task_before_removing

    if expected_response:
        response = client.delete(
            construct_path(CRUD_TASKS_PATH, task_id),
            json=task_id,
            headers=TEST_HEADERS,
        ).json()
    else:
        response = client.delete(
            construct_path(CRUD_TASKS_PATH, task_id),
            json=task_id,
            headers=TEST_HEADERS,
        ).content

    task = (
        prepare_db_for_ud_task.query(ManualAnnotationTask)
        .filter(ManualAnnotationTask.id == task_id)
        .first()
    )
    assert response == expected_response
    assert task == expected_task_in_db
    check_files_distributed_pages(prepare_db_for_ud_task, job_id)


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task", "request_body", "error_message"],
    [
        (
            CRUD_UD_CONSTRAINTS_TASKS[0],
            {"user_id": NOT_EXISTING_USER_ID},
            f"{NOT_EXISTING_USER_ID} is not assigned as annotator",
        ),
        (
            CRUD_UD_CONSTRAINTS_TASKS[7],
            {"user_id": NOT_EXISTING_USER_ID},
            f"{NOT_EXISTING_USER_ID} is not assigned as validator",
        ),
        (
            CRUD_UD_CONSTRAINTS_TASKS[6],
            {"is_validation": False},
            f"{CRUD_UD_CONSTRAINTS_TASKS[6].user_id} is not assigned "
            f"as annotator",
        ),  # same job validator but not annotator
        (
            CRUD_UD_CONSTRAINTS_TASKS[6],
            {"user_id": CRUD_UD_CONSTRAINTS_USERS[0].user_id},
            f"{CRUD_UD_CONSTRAINTS_USERS[0].user_id} is not assigned "
            f"as validator",
        ),  # same job annotator but not validator
        (
            CRUD_UD_CONSTRAINTS_TASKS[0],
            {
                "job_id": CRUD_UD_CONSTRAINTS_JOBS[2].job_id,
                "is_validation": True,
            },
            f"{CRUD_UD_CONSTRAINTS_USERS[0].user_id} is not assigned "
            f"as validator",
        ),  # same user not from new job
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_update_task_user_job_constraints(
    prepare_db_for_ud_task_constrains, task, request_body, error_message
):
    """Tests constrains between users, jobs and tasks types."""
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, task.id),
        headers=TEST_HEADERS,
        json=request_body,
    )
    assert response.status_code == 400
    assert error_message in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task", "request_body"],
    [
        (
            CRUD_UD_CONSTRAINTS_TASKS[0],
            {"job_id": CRUD_UD_CONSTRAINTS_JOBS[2].job_id},
        ),  # update annotation task assignment to validation only job
        (
            CRUD_UD_CONSTRAINTS_TASKS[7],
            {"is_validation": False},
        ),  # update validation task type of validation only job to annotation
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_update_task_type_job_constraints(
    prepare_db_for_ud_task_constrains, task, request_body
):
    """Tests that tasks cannot be updated if it will be annotation task for
    validation only job."""
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, task.id),
        headers=TEST_HEADERS,
        json=request_body,
    )
    assert response.status_code == 400
    assert "Error: this job is validation only." in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task", "request_body", "file_id", "job_id"],
    [
        (
            CRUD_UD_CONSTRAINTS_TASKS[8],
            {"file_id": CRUD_UD_CONSTRAINTS_FILES[0].file_id},
            CRUD_UD_CONSTRAINTS_FILES[0].file_id,
            CRUD_UD_CONSTRAINTS_TASKS[8].job_id,
        ),  # new file from other job
        (
            CRUD_UD_CONSTRAINTS_TASKS[8],
            {"file_id": NOT_EXISTING_FILE_ID},
            NOT_EXISTING_FILE_ID,
            CRUD_UD_CONSTRAINTS_TASKS[8].job_id,
        ),  # not existing file
        (
            CRUD_UD_CONSTRAINTS_TASKS[8],
            {"job_id": CRUD_UD_CONSTRAINTS_JOBS[0].job_id},
            CRUD_UD_CONSTRAINTS_TASKS[8].file_id,
            CRUD_UD_CONSTRAINTS_JOBS[0].job_id,
        ),  # new file from other job
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_update_task_file_job_constraints(
    prepare_db_for_ud_task_constrains, task, request_body, file_id, job_id
):
    """Tests constrains between files and jobs."""
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, task.id),
        headers=TEST_HEADERS,
        json=request_body,
    )
    error_message = f"file with id {file_id} is not assigned for job {job_id}"
    assert response.status_code == 400
    assert error_message in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["request_body", "extra_pages"],
    [
        (
            {"job_id": CRUD_UD_CONSTRAINTS_JOBS[1].job_id},
            {3, 4},
        ),  # same file new job
        (
            {"file_id": CRUD_UD_CONSTRAINTS_FILES[0].file_id},
            {4},
        ),  # same job new file
        (
            {"pages": list(range(1, 10))},
            {9},
        ),  # same job and file new pages
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_update_task_cross_job_pages_constraint(
    prepare_db_for_ud_task_constrains, request_body, extra_pages
):
    """Tests constrains between task pages and file pages."""
    task = CRUD_UD_CONSTRAINTS_TASKS[0]
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, task.id),
        headers=TEST_HEADERS,
        json=request_body,
    )
    assert response.status_code == 400
    assert f"pages ({extra_pages}) do not belong to file" in response.text


@pytest.mark.integration
@pytest.mark.parametrize("task", CRUD_UD_CONSTRAINTS_TASKS[3:6])
@pytest.mark.skip(reason="tests refactoring")
def test_update_task_wrong_statuses(prepare_db_for_ud_task_constrains, task):
    """Checks that we can't update tasks that are not in 'Pending' status."""
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, task.id),
        json={"is_validation": True},
        headers=TEST_HEADERS,
    )
    assert response.status_code == 400
    assert "only tasks in 'Pending' status could be updated" in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task", "status_code"],
    [(CRUD_UD_CONSTRAINTS_TASKS[0], 200), (CRUD_UD_CONSTRAINTS_TASKS[1], 400)],
)
@pytest.mark.skip(reason="tests refactoring")
def test_update_task_type_cross_pages_exception(
    prepare_db_for_ud_task_constrains, task, status_code
):
    """Tests that in cross validation job update from annotation to validation
    type of task with same id in same file of same job with pages that are
    distributed for annotation for same user in same task doesn't raise error.
    But if there is such task with other id - error will be raised.
    """
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, task.id),
        json={"is_validation": True},
        headers=TEST_HEADERS,
    )
    assert response.status_code == status_code
    if response.status_code != 200:
        error_message = (
            "user can't validate file's pages that are already distributed "
            f"in annotation tasks for this user: {set(task.pages)}"
        )
        assert error_message in response.text


@pytest.mark.integration
@pytest.mark.parametrize("task", CRUD_UD_CONSTRAINTS_TASKS[3:6])
@pytest.mark.skip(reason="tests refactoring")
def test_update_task_empty_request(prepare_db_for_ud_task_constrains, task):
    """Checks that empty request body returns 204_NO_CONTENT"""
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, task.id),
        json={},
        headers=TEST_HEADERS,
    )
    result_data = response.json()
    assert response.status_code == 200
    assert result_data["id"] == task.id


@pytest.mark.integration
@pytest.mark.parametrize("task", CRUD_UD_CONSTRAINTS_TASKS[0:2])
@pytest.mark.skip(reason="tests refactoring")
def test_update_task_deadline_with_none_value(
    prepare_db_for_ud_task_constrains, task
):
    """Checks if task deadline can be updated with None value"""
    response = client.patch(
        construct_path(CRUD_TASKS_PATH, task.id),
        json={"deadline": None},
        headers=TEST_HEADERS,
    )
    result_data = response.json()
    assert response.status_code == 200
    assert "deadline" in result_data.keys()
    assert result_data["deadline"] is None
