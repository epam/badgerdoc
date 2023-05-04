from unittest.mock import Mock, patch

import pytest
import responses
from fastapi.testclient import TestClient
from sqlalchemy import not_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from annotation.microservice_communication.assets_communication import (
    ASSETS_URL,
)
from annotation.models import Category, File, Job, ManualAnnotationTask, User
from annotation.schemas import CategoryTypeSchema, ValidationSchema
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app

client = TestClient(app)

POST_TASKS_PATH = "/distribution"
TEST_POST_USERS = [
    User(user_id="0c4963ad-200b-491e-925a-054814ebc721"),
    User(
        user_id="d6aff1ef-df86-416f-ac0d-fe10c7e61df7",
        default_load=10,
    ),
    User(user_id="ee35574f-9a9a-4934-8e2f-3c28424e3795"),
]
POST_TASKS_CATEGORIES = [
    Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    ),
]

VALIDATION_TYPE = ValidationSchema.cross
TASK_INFO_FILES_IDS = [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
]
JOBS_ID = [1, 2, 3, 4, 5, 6]
TASK_INFO_FILES = [
    {
        "user_ids": [
            TEST_POST_USERS[0].user_id,
            TEST_POST_USERS[1].user_id,
            TEST_POST_USERS[2].user_id,
        ],
        "files": TASK_INFO_FILES_IDS[:6],
        "datasets": [],
        "job_id": JOBS_ID[0],
        "deadline": "2021-11-30T01:01:01",
    },
    {
        "user_ids": [
            TEST_POST_USERS[0].user_id,
            TEST_POST_USERS[1].user_id,
            TEST_POST_USERS[2].user_id,
        ],
        "files": TASK_INFO_FILES_IDS[6:8],
        "datasets": [],
        "job_id": JOBS_ID[1],
    },
]

TASK_INFO_DATASETS_IDS = [
    1,
    2,
]
TASK_INFO_DATASETS = [
    {
        "user_ids": [
            TEST_POST_USERS[0].user_id,
            TEST_POST_USERS[1].user_id,
            TEST_POST_USERS[2].user_id,
        ],
        "files": [],
        "datasets": [TASK_INFO_DATASETS_IDS[0]],
        "job_id": JOBS_ID[0],
    },
    {
        "user_ids": [
            TEST_POST_USERS[0].user_id,
            TEST_POST_USERS[1].user_id,
            TEST_POST_USERS[2].user_id,
        ],
        "files": [],
        "datasets": [TASK_INFO_DATASETS_IDS[1]],
        "job_id": JOBS_ID[1],
    },
]

TASK_INFO_USERS_VALIDATION = [
    {
        "user_ids": [],
        "files": [TASK_INFO_FILES_IDS[0]],
        "datasets": [],
        "job_id": JOBS_ID[0],
    },  # cross job - no users
    {
        "user_ids": [TEST_POST_USERS[0].user_id],
        "files": [TASK_INFO_FILES_IDS[0]],
        "datasets": [],
        "job_id": JOBS_ID[0],
    },  # cross job - one user
    {
        "user_ids": [TEST_POST_USERS[0].user_id],
        "files": [TASK_INFO_FILES_IDS[0]],
        "datasets": [],
        "job_id": JOBS_ID[4],
    },  # hierarchical job - no validator
    {
        "user_ids": [TEST_POST_USERS[-1].user_id],
        "files": [TASK_INFO_FILES_IDS[0]],
        "datasets": [],
        "job_id": JOBS_ID[4],
    },  # hierarchical job - no annotator
    {
        "user_ids": [TEST_POST_USERS[-1].user_id],
        "files": [TASK_INFO_FILES_IDS[10]],
        "datasets": [],
        "job_id": JOBS_ID[5],
    },  # ExtractionJob task
]


FILES_FROM_ASSETS_FOR_TASK_INFO = [
    [
        {
            "id": TASK_INFO_FILES_IDS[0],
            "pages": 5,
        },
        {
            "id": TASK_INFO_FILES_IDS[1],
            "pages": 3,
        },
        {
            "id": TASK_INFO_FILES_IDS[2],
            "pages": 3,
        },
        {
            "id": TASK_INFO_FILES_IDS[3],
            "pages": 4,
        },
        {
            "id": TASK_INFO_FILES_IDS[4],
            "pages": 1,
        },
        {
            "id": TASK_INFO_FILES_IDS[5],
            "pages": 11,
        },
    ],
    [
        {
            "id": TASK_INFO_FILES_IDS[6],
            "pages": 143,
        },
        {
            "id": TASK_INFO_FILES_IDS[7],
            "pages": 211,
        },
    ],
    [
        {
            "id": TASK_INFO_FILES_IDS[9],
            "pages": 9,
        },
        {
            "id": TASK_INFO_FILES_IDS[8],
            "pages": 9,
        },
    ],
]

TASK_INFO_NEW_USER = {
    "user_ids": [
        "af50ca51-ed33-4d9a-a8da-8ea174a9ac3b",
        "af50ca51-ed33-4d9a-a8da-8ea174a9ac4b",
    ],
    "files": [
        9,
    ],
    "datasets": [],
    "job_id": JOBS_ID[2],
    "deadline": "2021-10-19T01:01:01",
}
FILES_FROM_ASSETS_FOR_TASK_INFO_NEW_USER = [
    {
        "id": 9,
        "pages": 15,
    }
]
POST_FILES = [
    {
        "file_id": TASK_INFO_FILES_IDS[0],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[0],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[0][0]["pages"],
    },
    {
        "file_id": TASK_INFO_FILES_IDS[1],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[0],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[0][1]["pages"],
    },
    {
        "file_id": TASK_INFO_FILES_IDS[2],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[0],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[0][2]["pages"],
    },
    {
        "file_id": TASK_INFO_FILES_IDS[3],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[0],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[0][3]["pages"],
    },
    {
        "file_id": TASK_INFO_FILES_IDS[4],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[0],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[0][4]["pages"],
    },
    {
        "file_id": TASK_INFO_FILES_IDS[5],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[0],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[0][5]["pages"],
    },
    {
        "file_id": TASK_INFO_FILES_IDS[6],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[1],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[1][0]["pages"],
    },
    {
        "file_id": TASK_INFO_FILES_IDS[7],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[1],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[1][1]["pages"],
    },
    {
        "file_id": TASK_INFO_FILES_IDS[8],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[2],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[2][1]["pages"],
    },
    {
        "file_id": TASK_INFO_FILES_IDS[9],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[3],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[2][0]["pages"],
        "distributed_annotating_pages": list(
            range(1, FILES_FROM_ASSETS_FOR_TASK_INFO[2][0]["pages"] + 1)
        ),
        "annotated_pages": list(
            range(1, FILES_FROM_ASSETS_FOR_TASK_INFO[2][0]["pages"] + 1)
        ),
    },
    {
        "file_id": TASK_INFO_FILES_IDS[8],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[4],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[2][1]["pages"],
    },
    {
        "file_id": TASK_INFO_FILES_IDS[8],
        "tenant": TEST_TENANT,
        "job_id": JOBS_ID[5],
        "pages_number": FILES_FROM_ASSETS_FOR_TASK_INFO[2][1]["pages"],
    },  # ExtractionJob file
]
POST_FILES_PG = [File(**f) for f in POST_FILES]
POST_JOBS = (
    {
        "job_id": JOBS_ID[0],
        "callback_url": "http://www.test.com",
        "annotators": TEST_POST_USERS,
        "validators": [],
        "owners": [],
        "files": POST_FILES_PG[:6],
        "is_auto_distribution": False,
        "categories": POST_TASKS_CATEGORIES,
        "deadline": None,
        "tenant": TEST_TENANT,
        "validation_type": VALIDATION_TYPE,
    },
    {
        "job_id": JOBS_ID[1],
        "callback_url": "http://www.test.com",
        "annotators": TEST_POST_USERS,
        "validators": [],
        "owners": [],
        "files": POST_FILES_PG[6:8],
        "is_auto_distribution": False,
        "categories": POST_TASKS_CATEGORIES,
        "deadline": "2022-10-19T01:01:01",
        "tenant": TEST_TENANT,
        "validation_type": VALIDATION_TYPE,
    },
    {
        "job_id": JOBS_ID[2],
        "callback_url": "http://www.test.com",
        "annotators": [
            User(user_id="be623572-9d48-4c09-a084-8ad1f6abb942"),
            User(user_id="be623572-9d48-4c09-a084-8ad1f6abb943"),
        ],
        "files": [POST_FILES_PG[8]],
        "is_auto_distribution": False,
        "categories": POST_TASKS_CATEGORIES,
        "deadline": "2021-10-19T01:01:01",
        "tenant": TEST_TENANT,
        "validation_type": VALIDATION_TYPE,
    },
    {
        "job_id": JOBS_ID[3],
        "callback_url": "http://www.test.com",
        "annotators": [],
        "validators": TEST_POST_USERS[:-1],
        "owners": [],
        "files": [POST_FILES_PG[9]],
        "is_auto_distribution": False,
        "categories": POST_TASKS_CATEGORIES,
        "deadline": "2021-10-19T01:01:01",
        "tenant": TEST_TENANT,
        "validation_type": ValidationSchema.validation_only,
    },
    {
        "job_id": JOBS_ID[4],
        "callback_url": "http://www.test.com",
        "annotators": TEST_POST_USERS[0:2],
        "validators": TEST_POST_USERS[1:],
        "owners": [],
        "files": [POST_FILES_PG[10]],
        "is_auto_distribution": False,
        "categories": POST_TASKS_CATEGORIES,
        "deadline": "2021-10-19T01:01:01",
        "tenant": TEST_TENANT,
        "validation_type": ValidationSchema.hierarchical,
    },
    {
        "job_id": JOBS_ID[5],
        "callback_url": "http://www.test.com",
        "annotators": [],
        "validators": [],
        "owners": [],
        "files": [POST_FILES_PG[11]],
        "is_auto_distribution": False,
        "categories": POST_TASKS_CATEGORIES,
        "deadline": "2021-10-19T01:01:01",
        "tenant": TEST_TENANT,
        "validation_type": ValidationSchema.cross,
    },  # ExtractionJob
)
TASK_WRONG_JOB = {
    "user_ids": [
        TEST_POST_USERS[0].user_id,
        TEST_POST_USERS[1].user_id,
        TEST_POST_USERS[2].user_id,
    ],
    "files": [
        TASK_INFO_FILES_IDS[6],
        TASK_INFO_FILES_IDS[7],
    ],
    "datasets": [],
    "job_id": 7,
}
EMPTY_FILES_AND_DATASETS = {
    "user_ids": [
        TEST_POST_USERS[0].user_id,
        TEST_POST_USERS[1].user_id,
        TEST_POST_USERS[2].user_id,
    ],
    "files": [],
    "datasets": [],
    "job_id": 6,
    "deadline": "2021-10-19T01:01:01",
}


def check_files_distributed_pages(test_session: Session, job_id: int):
    tasks = test_session.query(ManualAnnotationTask).filter(
        ManualAnnotationTask.job_id == job_id,
    )
    files = test_session.query(File).filter(File.job_id == job_id).all()
    validation_type = (
        test_session.query(Job.validation_type)
        .filter_by(job_id=job_id)
        .first()
    )
    test_session.add_all(files)
    test_session.commit()
    for task_file in files:
        annotating_tasks = tasks.filter(
            ManualAnnotationTask.file_id == task_file.file_id,
            not_(ManualAnnotationTask.is_validation),
        ).all()
        distributed_annotating_pages = set()
        for annotating_task in annotating_tasks:
            distributed_annotating_pages.update(annotating_task.pages)
        distributed_annotating_pages = sorted(distributed_annotating_pages)
        if validation_type[0] != ValidationSchema.validation_only:
            assert (
                task_file.distributed_annotating_pages
                == distributed_annotating_pages
            )

        validating_tasks = tasks.filter(
            ManualAnnotationTask.file_id == task_file.file_id,
            ManualAnnotationTask.is_validation,
        ).all()
        distributed_validating_pages = set()
        for validating_task in validating_tasks:
            distributed_validating_pages.update(validating_task.pages)
        distributed_validating_pages = sorted(distributed_validating_pages)
        assert (
            task_file.distributed_validating_pages
            == distributed_validating_pages
        )


@pytest.mark.integration
def test_post_tasks_empty_files_and_datasets_error(
    prepare_db_for_post,
):
    response = client.post(
        "{0}".format(POST_TASKS_PATH),
        json=EMPTY_FILES_AND_DATASETS,
        headers=TEST_HEADERS,
    )
    assert response.status_code == 422


@pytest.mark.integration
@patch.object(Session, "query")
def test_post_tasks_exception(Session, monkeypatch, prepare_db_for_post):
    monkeypatch.setattr(
        "annotation.jobs.resources.get_files_info",
        Mock(return_value=FILES_FROM_ASSETS_FOR_TASK_INFO[0]),
    )
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.post(
        "{0}".format(POST_TASKS_PATH),
        json=TASK_INFO_FILES[0],
        headers=TEST_HEADERS,
    )
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_info", "returned_files", "expected_tasks_number"],
    [
        (TASK_INFO_FILES[0], FILES_FROM_ASSETS_FOR_TASK_INFO[0], 15),
        (TASK_INFO_FILES[1], FILES_FROM_ASSETS_FOR_TASK_INFO[1], 18),
    ],
)
@patch("annotation.distribution.main.SPLIT_MULTIPAGE_DOC", "true")
def test_post_tasks_only_files(
    monkeypatch,
    prepare_db_for_post,
    task_info,
    returned_files,
    expected_tasks_number,
):
    monkeypatch.setattr(
        "annotation.microservice_communication.assets_communication.get_response",  # noqa
        Mock(return_value=returned_files),
    )
    response = client.post(
        "{0}".format(POST_TASKS_PATH), json=task_info, headers=TEST_HEADERS
    )
    assert response.status_code == 201
    assert len(response.json()) == expected_tasks_number
    check_files_distributed_pages(prepare_db_for_post, task_info["job_id"])


@pytest.mark.integration
@pytest.mark.parametrize(["case_index", "tasks_number"], [(0, 14), (1, 19)])
@responses.activate
@patch("annotation.distribution.main.SPLIT_MULTIPAGE_DOC", "true")
def test_post_tasks_only_datasets(
    monkeypatch, prepare_db_for_post, case_index, tasks_number
):
    dataset_url = f"{ASSETS_URL}/{TASK_INFO_DATASETS_IDS[case_index]}/files"
    responses.add(
        responses.GET,
        dataset_url,
        json=FILES_FROM_ASSETS_FOR_TASK_INFO[case_index],
        status=200,
        headers=TEST_HEADERS,
    )

    response = client.post(
        "{0}".format(POST_TASKS_PATH),
        json=TASK_INFO_DATASETS[case_index],
        headers=TEST_HEADERS,
    )
    assert response.status_code == 201
    assert len(response.json()) == tasks_number
    check_files_distributed_pages(
        prepare_db_for_post, TASK_INFO_DATASETS[case_index]["job_id"]
    )


@pytest.mark.integration
def test_post_tasks_new_user(monkeypatch, prepare_db_for_post):
    assert not prepare_db_for_post.query(User).get(
        TASK_INFO_NEW_USER["user_ids"][0]
    )
    assert not prepare_db_for_post.query(User).get(
        TASK_INFO_NEW_USER["user_ids"][1]
    )
    monkeypatch.setattr(
        "annotation.microservice_communication.assets_communication.get_response",  # noqa
        Mock(return_value=FILES_FROM_ASSETS_FOR_TASK_INFO_NEW_USER),
    )
    response = client.post(
        "{0}".format(POST_TASKS_PATH),
        json=TASK_INFO_NEW_USER,
        headers=TEST_HEADERS,
    )
    expected_message = (
        f"are not assigned to job {TASK_INFO_NEW_USER['job_id']} "
        f"as annotators or validators"
    )
    assert response.status_code == 400
    for user in TASK_INFO_NEW_USER["user_ids"]:
        assert user in response.text
    assert expected_message in response.text
    assert not prepare_db_for_post.query(User).get(
        TASK_INFO_NEW_USER["user_ids"][0]
    )
    assert not prepare_db_for_post.query(User).get(
        TASK_INFO_NEW_USER["user_ids"][1]
    )
    check_files_distributed_pages(
        prepare_db_for_post, TASK_INFO_NEW_USER["job_id"]
    )


@pytest.mark.integration
def test_post_tasks_wrong_job(prepare_db_for_post):
    response = client.post(
        f"{POST_TASKS_PATH}", json=TASK_WRONG_JOB, headers=TEST_HEADERS
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": f"Error: wrong job_id ({TASK_WRONG_JOB['job_id']})"
    }


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_info", "expected_deadline", "assets_files"],
    [
        (
            TASK_INFO_FILES[0],
            TASK_INFO_FILES[0]["deadline"],
            FILES_FROM_ASSETS_FOR_TASK_INFO[0],
        ),
        (
            TASK_INFO_FILES[1],
            POST_JOBS[1]["deadline"],
            FILES_FROM_ASSETS_FOR_TASK_INFO[1],
        ),
    ],
)
def test_post_tasks_deadline(
    monkeypatch,
    prepare_db_for_post,
    task_info,
    expected_deadline,
    assets_files,
):
    monkeypatch.setattr(
        "annotation.microservice_communication.assets_communication.get_response",  # noqa
        Mock(return_value=assets_files),
    )
    response = client.post(
        f"{POST_TASKS_PATH}", json=task_info, headers=TEST_HEADERS
    )
    assert response.status_code == 201
    for task in response.json():
        assert task["deadline"] == expected_deadline
    check_files_distributed_pages(prepare_db_for_post, task_info["job_id"])


@pytest.mark.integration
def test_post_tasks_validation_only(monkeypatch, prepare_db_for_post):
    monkeypatch.setattr(
        "annotation.microservice_communication.assets_communication.get_response",  # noqa
        Mock(return_value=[FILES_FROM_ASSETS_FOR_TASK_INFO[2][0]]),
    )
    tasks_info = {
        "user_ids": [str(user.user_id) for user in TEST_POST_USERS[:-1]],
        "files": [TASK_INFO_FILES_IDS[9]],
        "datasets": [],
        "job_id": JOBS_ID[3],
    }
    response = client.post(
        f"{POST_TASKS_PATH}", json=tasks_info, headers=TEST_HEADERS
    )
    assert response.status_code == 201
    for task in response.json():
        assert task["is_validation"]
    check_files_distributed_pages(prepare_db_for_post, tasks_info["job_id"])


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_info", "returned_files"],
    [
        (TASK_INFO_FILES[0], FILES_FROM_ASSETS_FOR_TASK_INFO[1]),
        (TASK_INFO_FILES[1], FILES_FROM_ASSETS_FOR_TASK_INFO[0]),
    ],
)
def test_post_tasks_wrong_files(
    monkeypatch,
    prepare_db_for_post,
    task_info,
    returned_files,
):
    monkeypatch.setattr(
        "annotation.microservice_communication.assets_communication.get_response",  # noqa
        Mock(return_value=returned_files),
    )
    response = client.post(
        "{0}".format(POST_TASKS_PATH), json=task_info, headers=TEST_HEADERS
    )
    wrong_files = {assets_file["id"] for assets_file in returned_files}
    job_id = task_info["job_id"]
    assert f"{wrong_files} are not assigned to job {job_id}" in response.text
    assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.parametrize(
    ["status_code", "error_message", "tasks_info", "assets_files"],
    [
        (
            422,
            "ensure this value has at least 1 items",
            TASK_INFO_USERS_VALIDATION[0],
            FILES_FROM_ASSETS_FOR_TASK_INFO[0],
        ),
        (
            400,
            "There must be more than one annotator provided for cross",
            TASK_INFO_USERS_VALIDATION[1],
            FILES_FROM_ASSETS_FOR_TASK_INFO[0],
        ),
        (
            400,
            "hierarchical, validators should be provided",
            TASK_INFO_USERS_VALIDATION[2],
            [FILES_FROM_ASSETS_FOR_TASK_INFO[2][1]],
        ),
        (
            400,
            "must be at least one annotator provided for hierarchical",
            TASK_INFO_USERS_VALIDATION[3],
            [FILES_FROM_ASSETS_FOR_TASK_INFO[2][1]],
        ),
        (
            400,
            "are not assigned to job",
            TASK_INFO_USERS_VALIDATION[4],
            [FILES_FROM_ASSETS_FOR_TASK_INFO[2][1]],
        ),
    ],
)
def test_post_tasks_users_validation_error(
    monkeypatch,
    prepare_db_for_post,
    status_code,
    error_message,
    tasks_info,
    assets_files,
):
    monkeypatch.setattr(
        "annotation.microservice_communication.assets_communication.get_response",  # noqa
        Mock(return_value=assets_files),
    )
    response = client.post(
        "{0}".format(POST_TASKS_PATH), json=tasks_info, headers=TEST_HEADERS
    )
    assert response.status_code == status_code
    assert error_message in response.text
