from unittest.mock import Mock, patch

import pytest
import responses
from fastapi.testclient import TestClient
from requests import ConnectionError, RequestException, Timeout
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.microservice_communication.assets_communication import (
    ASSETS_FILES_URL,
)
from app.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from app.models import Category, File, Job, ManualAnnotationTask, User
from app.schemas import (
    CategoryTypeSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from tests.override_app_dependency import (
    TEST_HEADERS,
    TEST_TENANT,
    TEST_TOKEN,
    app,
)

client = TestClient(app)

POST_NEXT_TASK_PATH = "/tasks/next"
CATEGORIES = [
    Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    ),
]
ANNOTATORS = (
    User(user_id="dbfc5eb0-ead2-446a-bc3f-cf0b44c85884"),
    User(user_id="87a1981d-26a2-4362-a6c2-df3d882f5a50"),
    User(user_id="315caff3-17e8-41a6-8086-aa80b5dcf6c6"),
    User(user_id="4b88db6c-f636-4ab2-baa7-21add1e4ab52"),
)
WRONG_ANNOTATOR = "5935263d-49a5-46d5-98d2-5916e021aa7f"

NEXT_TASK_JOB = Job(
    job_id=1,
    name="extractionJob1",
    callback_url="http://www.test.com/test1",
    annotators=[*ANNOTATORS],
    validation_type=ValidationSchema.cross,
    is_auto_distribution=False,
    categories=CATEGORIES,
    deadline=None,
    tenant=TEST_TENANT,
)
FILE = File(
    file_id=2,
    tenant=TEST_TENANT,
    job_id=NEXT_TASK_JOB.job_id,
    pages_number=100,
)
NEXT_TASK_ANNOTATION_TASKS = [
    ManualAnnotationTask(
        id=1,
        file_id=FILE.file_id,
        pages=[1, 2, 3],
        job_id=NEXT_TASK_JOB.job_id,
        user_id=ANNOTATORS[0].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.ready,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=2,
        file_id=FILE.file_id,
        pages=[1, 2, 3],
        job_id=NEXT_TASK_JOB.job_id,
        user_id=ANNOTATORS[0].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.in_progress,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=3,
        file_id=FILE.file_id,
        pages=[1, 2, 3],
        job_id=NEXT_TASK_JOB.job_id,
        user_id=ANNOTATORS[1].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.pending,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=4,
        file_id=FILE.file_id,
        pages=[1, 2, 3],
        job_id=NEXT_TASK_JOB.job_id,
        user_id=ANNOTATORS[1].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.ready,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=5,
        file_id=FILE.file_id,
        pages=[1, 2, 3],
        job_id=NEXT_TASK_JOB.job_id,
        user_id=ANNOTATORS[2].user_id,
        is_validation=True,
        status=TaskStatusEnumSchema.ready,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=6,
        file_id=FILE.file_id,
        pages=[1, 2, 3],
        job_id=NEXT_TASK_JOB.job_id,
        user_id=ANNOTATORS[3].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.pending,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=7,
        file_id=FILE.file_id,
        pages=[1, 2, 3],
        job_id=NEXT_TASK_JOB.job_id,
        user_id=ANNOTATORS[3].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.finished,
        deadline=None,
    ),
]

FILES_FROM_ASSETS = [
    {
        "id": 2,
        "original_name": "some_1.pdf",
        "bucket": "merck",
        "size_in_bytes": 165887,
        "content_type": "image/png",
        "pages": 10,
        "last_modified": "2021-09-28T01:27:55",
        "path": "files/1/1.pdf",
        "datasets": [],
    }
]
JOBS_FROM_JOBS_SERVICE = {
    "pagination": {
        "page_num": 1,
        "page_size": 15,
        "min_pages_left": 1,
        "total": 3,
        "has_more": False,
    },
    "data": [
        {
            "id": 1,
            "name": "extractionJob1",
            "status": "Pending",
            "files": [1, 2],
            "datasets": [2],
            "creation_datetime": "2021-11-23T12:26:41.669562",
            "type": "ExtractionJob",
            "mode": "Automatic",
            "all_files_data": [
                {
                    "id": 3,
                    "path": "files/3/3.pdf",
                    "pages": 6,
                    "bucket": "merck",
                    "status": "uploaded",
                    "datasets": ["dataset22"],
                    "extension": ".pdf",
                    "content_type": "application/pdf",
                    "last_modified": "2021-11-19T12:26:19.086643",
                    "original_name": "33.pdf",
                    "size_in_bytes": 917433,
                },
            ],
            "pipeline_id": "2",
        },
    ],
}
ASSETS_RESPONSE = {
    "pagination": {
        "page_num": 1,
        "page_size": 15,
        "min_pages_left": 1,
        "total": 3,
        "has_more": False,
    },
    "data": FILES_FROM_ASSETS,
}
EXPANDED_NEXT_TASK_RESPONSES = [
    dict(
        id=2,
        pages=[1, 2, 3],
        user_id=ANNOTATORS[0].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.in_progress,
        deadline=None,
        file={
            "id": FILE.file_id,
            "name": FILES_FROM_ASSETS[0]["original_name"],
        },
        job={
            "id": NEXT_TASK_JOB.job_id,
            "name": JOBS_FROM_JOBS_SERVICE["data"][0]["name"],
        },
    ),
    dict(
        id=4,
        pages=[1, 2, 3],
        user_id=ANNOTATORS[1].user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.in_progress,
        deadline=None,
        file={
            "id": FILE.file_id,
            "name": FILES_FROM_ASSETS[0]["original_name"],
        },
        job={
            "id": NEXT_TASK_JOB.job_id,
            "name": JOBS_FROM_JOBS_SERVICE["data"][0]["name"],
        },
    ),
]


@pytest.mark.integration
@patch.object(Session, "query")
def test_post_next_task_sql_connection_error(
    Session,
    prepare_db_for_get_next_task,
    user_id=ANNOTATORS[0].user_id,
):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.post(
        POST_NEXT_TASK_PATH,
        headers={
            "user": str(user_id),
            HEADER_TENANT: TEST_TENANT,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["exc"], [(ConnectionError(),), (Timeout(),), (RequestException(),)]
)
@responses.activate
def test_post_next_task_request_error(prepare_db_for_get_next_task, exc):
    responses.add(
        responses.GET,
        ASSETS_FILES_URL,
        body=exc,
        headers=TEST_HEADERS,
        status=200,
    )
    response = client.post(
        POST_NEXT_TASK_PATH,
        headers={
            "user": str(ANNOTATORS[0].user_id),
            HEADER_TENANT: TEST_TENANT,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 500
    assert "Error:" in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    "user_id",
    [
        WRONG_ANNOTATOR,
        ANNOTATORS[2].user_id,
        ANNOTATORS[3].user_id,
    ],
)
def test_post_next_task_404_error(
    prepare_db_for_get_next_task,
    user_id,
):
    response = client.post(
        POST_NEXT_TASK_PATH,
        headers={
            "user": str(user_id),
            HEADER_TENANT: TEST_TENANT,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 404
    assert "Can't find working tasks for user" in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["user_id", "expected_response"],
    [
        (
            ANNOTATORS[0].user_id,
            EXPANDED_NEXT_TASK_RESPONSES[0],
        ),
        (
            ANNOTATORS[1].user_id,
            EXPANDED_NEXT_TASK_RESPONSES[1],
        ),
    ],
)
@responses.activate
def test_post_next_task(
    prepare_db_for_get_next_task,
    user_id,
    expected_response,
):
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSETS_RESPONSE,
        headers=TEST_HEADERS,
        status=200,
    )
    response = client.post(
        POST_NEXT_TASK_PATH,
        headers={
            "user": str(user_id),
            HEADER_TENANT: TEST_TENANT,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 200
    assert response.json() == expected_response
    assert (
        prepare_db_for_get_next_task.query(ManualAnnotationTask)
        .get(response.json()["id"])
        .status
        == TaskStatusEnumSchema.in_progress
    )
