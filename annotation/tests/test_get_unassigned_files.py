from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from annotation.models import Category, File, Job, User
from annotation.schemas import CategoryTypeSchema, ValidationSchema
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app

client = TestClient(app)

GET_JOB_UNASSIGNED_FILES_PATH = "/jobs/{job_id}/files/unassigned"
CATEGORY = Category(
    id="Test",
    name="Test",
    type=CategoryTypeSchema.box,
)

ANNOTATORS = (
    User(user_id="93f070cb-4332-41ca-b5a4-8b388bd4b931"),
    User(user_id="3a81beb8-9419-4630-b0c9-96bd8ed48d27"),
)
JOBS = (
    Job(
        job_id=1,
        callback_url="http://jobs/jobs/1",
        annotators=[
            ANNOTATORS[0],
            ANNOTATORS[1],
        ],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=[CATEGORY],
        deadline="2021-12-31T01:01:01",
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=2,
        callback_url="http://jobs/jobs/2",
        annotators=[
            ANNOTATORS[0],
            ANNOTATORS[1],
        ],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=[CATEGORY],
        deadline="2021-12-31T01:01:01",
        tenant=TEST_TENANT,
    ),
)
WRONG_JOB_ID = 3
FILES_IDS = (
    1,
    2,
    3,
    4,
    5,
)
FILES = (
    File(
        file_id=FILES_IDS[0],
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=6,
        distributed_annotating_pages=[1, 4, 5],
        distributed_validating_pages=[1, 4],
    ),
    File(
        file_id=FILES_IDS[1],
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=8,
        distributed_annotating_pages=[1, 2, 3, 4, 5, 6, 7, 8],
        distributed_validating_pages=[],
    ),
    File(
        file_id=FILES_IDS[2],
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=5,
        distributed_annotating_pages=[],
        distributed_validating_pages=[1, 2, 3, 4, 5],
    ),
    File(
        file_id=FILES_IDS[3],
        tenant=TEST_TENANT,
        job_id=JOBS[0].job_id,
        pages_number=5,
        distributed_annotating_pages=[1, 2, 3, 4, 5],
        distributed_validating_pages=[1, 2, 3, 4, 5],
    ),
    File(
        file_id=FILES_IDS[4],
        tenant=TEST_TENANT,
        job_id=JOBS[1].job_id,
        pages_number=10,
        distributed_annotating_pages=[1, 2, 4, 6, 7],
        distributed_validating_pages=[1, 4, 7],
    ),
)
UNASSIGNED_FILES_ENTITIES = [CATEGORY, *ANNOTATORS, *JOBS, *FILES]


@pytest.mark.integration
@patch.object(Session, "query")
@pytest.mark.skip(reason="tests refactoring")
def test_get_unassigned_files_sql_connection_error(
    Session,
    db_get_unassigned_files,
    job_id=JOBS[0].job_id,
):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.get(
        GET_JOB_UNASSIGNED_FILES_PATH.format(job_id=job_id),
        headers=TEST_HEADERS,
    )
    assert response.status_code == 500
    assert "Error: connection error" in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_id", "expected_code", "expected_response"],
    [
        (
            JOBS[0].job_id,
            200,
            {
                "current_page": 1,
                "job_id": JOBS[0].job_id,
                "page_size": 50,
                "tenant": TEST_TENANT,
                "total_objects": 3,
                "unassigned_files": [
                    {
                        "id": FILES[0].file_id,
                        "pages_to_annotate": [2, 3, 6],
                        "pages_to_validate": [2, 3, 5, 6],
                    },
                    {
                        "id": FILES[1].file_id,
                        "pages_to_annotate": [],
                        "pages_to_validate": [1, 2, 3, 4, 5, 6, 7, 8],
                    },
                    {
                        "id": FILES[2].file_id,
                        "pages_to_annotate": [1, 2, 3, 4, 5],
                        "pages_to_validate": [],
                    },
                ],
            },
        ),
        (
            JOBS[1].job_id,
            200,
            {
                "current_page": 1,
                "job_id": JOBS[1].job_id,
                "page_size": 50,
                "tenant": TEST_TENANT,
                "total_objects": 1,
                "unassigned_files": [
                    {
                        "id": FILES[4].file_id,
                        "pages_to_annotate": [3, 5, 8, 9, 10],
                        "pages_to_validate": [2, 3, 5, 6, 8, 9, 10],
                    }
                ],
            },
        ),
        (
            WRONG_JOB_ID,
            404,
            {"detail": f"Error: Job with job_id ({WRONG_JOB_ID}) not found"},
        ),
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_get_unassigned_files_status_codes(
    db_get_unassigned_files,
    job_id,
    expected_code,
    expected_response,
):
    response = client.get(
        GET_JOB_UNASSIGNED_FILES_PATH.format(job_id=job_id),
        headers=TEST_HEADERS,
    )
    assert response.status_code == expected_code
    assert response.json() == expected_response


@pytest.mark.parametrize(
    ["job_id", "url_params", "expected_response"],
    [
        (
            JOBS[0].job_id,
            {"page_size": 2, "page_num": 1},
            {
                "current_page": 1,
                "job_id": JOBS[0].job_id,
                "page_size": 2,
                "tenant": TEST_TENANT,
                "total_objects": 3,
                "unassigned_files": [
                    {
                        "id": FILES[0].file_id,
                        "pages_to_annotate": [2, 3, 6],
                        "pages_to_validate": [2, 3, 5, 6],
                    },
                    {
                        "id": FILES[1].file_id,
                        "pages_to_annotate": [],
                        "pages_to_validate": [1, 2, 3, 4, 5, 6, 7, 8],
                    },
                ],
            },
        ),
        (
            JOBS[0].job_id,
            {"page_size": 1, "page_num": 2},
            {
                "current_page": 2,
                "job_id": JOBS[0].job_id,
                "page_size": 1,
                "tenant": TEST_TENANT,
                "total_objects": 3,
                "unassigned_files": [
                    {
                        "id": FILES[1].file_id,
                        "pages_to_annotate": [],
                        "pages_to_validate": [1, 2, 3, 4, 5, 6, 7, 8],
                    },
                ],
            },
        ),
        (
            JOBS[0].job_id,
            {"page_size": 50, "page_num": 2},
            {
                "current_page": 2,
                "job_id": JOBS[0].job_id,
                "page_size": 50,
                "tenant": TEST_TENANT,
                "total_objects": 3,
                "unassigned_files": [],
            },
        ),
        (
            JOBS[1].job_id,
            {"page_size": 1, "page_num": 2},
            {
                "current_page": 2,
                "job_id": JOBS[1].job_id,
                "page_size": 1,
                "tenant": TEST_TENANT,
                "total_objects": 1,
                "unassigned_files": [],
            },
        ),
    ],
)
@pytest.mark.skip(reason="tests refactoring")
def test_get_job_files_pagination(
    db_get_unassigned_files,
    job_id,
    url_params,
    expected_response,
):
    response = client.get(
        GET_JOB_UNASSIGNED_FILES_PATH.format(job_id=job_id),
        params=url_params,
        headers=TEST_HEADERS,
    )
    assert response.status_code == 200
    assert response.json() == expected_response
