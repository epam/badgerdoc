from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from annotation.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from annotation.models import Category, File, Job, User
from annotation.schemas import (
    CategoryTypeSchema,
    FileStatusEnumSchema,
    ValidationSchema,
)
from tests.override_app_dependency import TEST_TOKEN, app

client = TestClient(app)

GET_JOB_FILES_PATH = "/jobs/{job_id}/files"
CATEGORIES = [
    Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    ),
]
GET_JOB_FILES_TENANTS = (
    "tenant1",
    "tenant2",
)
GET_JOB_FILES_ANNOTATORS = (
    User(user_id="53ecc0aa-6f21-465f-9018-8c887c4d7fd1"),
    User(user_id="92df9d59-1865-4fde-95be-a2cc44ea61ed"),
    User(user_id="2d5f96b4-acba-41b2-ae76-a8e52c1c95df"),
)
GET_JOB_FILES_JOBS = (
    Job(
        job_id=1,
        callback_url="http://www.test.com",
        annotators=[
            GET_JOB_FILES_ANNOTATORS[0],
            GET_JOB_FILES_ANNOTATORS[1],
        ],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=GET_JOB_FILES_TENANTS[0],
    ),
    Job(
        job_id=2,
        callback_url="http://www.test.com",
        annotators=[GET_JOB_FILES_ANNOTATORS[0]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=GET_JOB_FILES_TENANTS[1],
    ),
    Job(
        job_id=3,
        callback_url="http://www.test.com",
        annotators=[GET_JOB_FILES_ANNOTATORS[2]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=GET_JOB_FILES_TENANTS[1],
    ),
)
WRONG_JOB_ID = 4
FILES_IDS = (
    1,
    2,
    3,
    4,
)
GET_JOB_FILES = (
    File(
        file_id=FILES_IDS[0],
        tenant=GET_JOB_FILES_TENANTS[0],
        job_id=GET_JOB_FILES_JOBS[0].job_id,
        pages_number=5,
        status=FileStatusEnumSchema.pending,
    ),
    File(
        file_id=FILES_IDS[1],
        tenant=GET_JOB_FILES_TENANTS[0],
        job_id=GET_JOB_FILES_JOBS[0].job_id,
        pages_number=30,
        status=FileStatusEnumSchema.pending,
    ),
    File(
        file_id=FILES_IDS[2],
        tenant=GET_JOB_FILES_TENANTS[0],
        job_id=GET_JOB_FILES_JOBS[0].job_id,
        pages_number=10,
        status=FileStatusEnumSchema.pending,
    ),
    File(
        file_id=FILES_IDS[2],
        tenant=GET_JOB_FILES_TENANTS[1],
        job_id=GET_JOB_FILES_JOBS[1].job_id,
        pages_number=40,
        status=FileStatusEnumSchema.pending,
    ),
    File(
        file_id=FILES_IDS[3],
        tenant=GET_JOB_FILES_TENANTS[0],
        job_id=GET_JOB_FILES_JOBS[1].job_id,
        pages_number=50,
        status=FileStatusEnumSchema.pending,
    ),
    File(
        file_id=FILES_IDS[3],
        tenant=GET_JOB_FILES_TENANTS[1],
        job_id=GET_JOB_FILES_JOBS[2].job_id,
        pages_number=100,
        status=FileStatusEnumSchema.pending,
    ),
)


@pytest.mark.integration
@patch.object(Session, "query")
def test_get_job_files_connection_error(
    Session,
    prepare_db_for_get_job_files,
    job_id=GET_JOB_FILES_JOBS[0].job_id,
):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.get(
        GET_JOB_FILES_PATH.format(job_id=job_id),
        headers={
            HEADER_TENANT: GET_JOB_FILES_TENANTS[0],
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_id", "tenant"],
    [
        (WRONG_JOB_ID, GET_JOB_FILES_TENANTS[0]),
        (GET_JOB_FILES_JOBS[0].job_id, GET_JOB_FILES_TENANTS[1]),
        (GET_JOB_FILES_JOBS[1].job_id, GET_JOB_FILES_TENANTS[0]),
    ],
)
def test_get_job_files_404_error(
    prepare_db_for_get_job_files,
    job_id,
    tenant,
):
    response = client.get(
        GET_JOB_FILES_PATH.format(job_id=job_id),
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 404
    assert f"Error: Job with job_id ({job_id}) not found" in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_id", "tenant", "expected_files"],
    [
        (
            GET_JOB_FILES_JOBS[0].job_id,
            GET_JOB_FILES_TENANTS[0],
            [{"id": f.file_id, "status": f.status} for f in GET_JOB_FILES[:3]],
        ),
        (
            GET_JOB_FILES_JOBS[1].job_id,
            GET_JOB_FILES_TENANTS[1],
            [
                {
                    "id": GET_JOB_FILES[3].file_id,
                    "status": GET_JOB_FILES[3].status,
                }
            ],
        ),
        (
            GET_JOB_FILES_JOBS[2].job_id,
            GET_JOB_FILES_TENANTS[1],
            [
                {
                    "id": GET_JOB_FILES[5].file_id,
                    "status": GET_JOB_FILES[5].status,
                }
            ],
        ),
    ],
)
def test_get_job_files(prepare_db_for_get_job_files, job_id, tenant, expected_files):
    response = client.get(
        GET_JOB_FILES_PATH.format(job_id=job_id),
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 200
    expected_full_response = {
        "tenant": tenant,
        "job_id": job_id,
        "total_objects": len(expected_files),
        "current_page": 1,
        "page_size": 50,
        "files": expected_files,
    }
    assert response.json() == expected_full_response


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_id", "tenant", "url_params", "expected_response"],
    [
        (
            GET_JOB_FILES_JOBS[0].job_id,
            GET_JOB_FILES_TENANTS[0],
            {"page_size": 50, "page_num": 1},
            {
                "tenant": GET_JOB_FILES_TENANTS[0],
                "job_id": GET_JOB_FILES_JOBS[0].job_id,
                "total_objects": 3,
                "current_page": 1,
                "page_size": 50,
                "files": [
                    {"id": f.file_id, "status": f.status} for f in GET_JOB_FILES[:3]
                ],
            },
        ),
        (
            GET_JOB_FILES_JOBS[0].job_id,
            GET_JOB_FILES_TENANTS[0],
            {"page_size": 1, "page_num": 2},
            {
                "tenant": GET_JOB_FILES_TENANTS[0],
                "job_id": GET_JOB_FILES_JOBS[0].job_id,
                "total_objects": 3,
                "current_page": 2,
                "page_size": 1,
                "files": [
                    {
                        "id": GET_JOB_FILES[1].file_id,
                        "status": GET_JOB_FILES[1].status,
                    }
                ],
            },
        ),
        (
            GET_JOB_FILES_JOBS[0].job_id,
            GET_JOB_FILES_TENANTS[0],
            {"page_size": 2, "page_num": 1},
            {
                "tenant": GET_JOB_FILES_TENANTS[0],
                "job_id": GET_JOB_FILES_JOBS[0].job_id,
                "total_objects": 3,
                "current_page": 1,
                "page_size": 2,
                "files": [
                    {"id": f.file_id, "status": f.status} for f in GET_JOB_FILES[:2]
                ],
            },
        ),
        (
            GET_JOB_FILES_JOBS[0].job_id,
            GET_JOB_FILES_TENANTS[0],
            {"page_size": 3, "page_num": 2},
            {
                "tenant": GET_JOB_FILES_TENANTS[0],
                "job_id": GET_JOB_FILES_JOBS[0].job_id,
                "total_objects": 3,
                "current_page": 2,
                "page_size": 3,
                "files": [],
            },
        ),
    ],
)
def test_get_job_files_pagination(
    prepare_db_for_get_job_files,
    job_id,
    tenant,
    url_params,
    expected_response,
):
    response = client.get(
        GET_JOB_FILES_PATH.format(job_id=job_id),
        params=url_params,
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 200
    assert response.json() == expected_response
