from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from annotation.jobs import collect_job_names
from annotation.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from annotation.models import Category, File, Job, User
from annotation.schemas import FileStatusEnumSchema, ValidationSchema
from tests.consts import ANNOTATION_PATH
from tests.override_app_dependency import TEST_TOKEN, app

client = TestClient(app)

JOB_TEST_TENANTS = (
    "tenant1",
    "tenant2",
)
PIPELINE_ID = 1
JOB_TEST_ANNOTATORS = (
    User(user_id="82533770-a99e-4873-8b23-6bbda86b59ae"),
    User(user_id="ef81a4d0-cc01-447b-9025-a70ed441672d"),
    User(user_id="2d3a59c3-c0e8-4322-82df-e693106c1cd0"),
)
CATEGORIES = [Category(id="18d3d189e73a4680bfa77ba3fe6ebee5", name="Test")]
FILE_TEST_IDS = [
    1,
    2,
]
JOB_TEST_IDS = [
    1,
    2,
    3,
    4,
    5,
]
GET_JOBS = (
    Job(
        job_id=1,
        name="Job1name",
        callback_url="http://www.test.com",
        annotators=[
            JOB_TEST_ANNOTATORS[0],
            JOB_TEST_ANNOTATORS[1],
        ],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=JOB_TEST_TENANTS[0],
    ),
    Job(
        job_id=2,
        name="Job2name",
        callback_url="http://www.test.com",
        annotators=[JOB_TEST_ANNOTATORS[0]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=JOB_TEST_TENANTS[1],
    ),
    Job(
        job_id=3,
        callback_url="http://www.test.com",
        annotators=[JOB_TEST_ANNOTATORS[2]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=JOB_TEST_TENANTS[1],
    ),
)
GET_FILES = (
    File(
        file_id=FILE_TEST_IDS[0],
        tenant=JOB_TEST_TENANTS[0],
        job_id=GET_JOBS[0].job_id,
        pages_number=5,
        status=FileStatusEnumSchema.pending,
    ),
    File(
        file_id=FILE_TEST_IDS[1],
        tenant=JOB_TEST_TENANTS[0],
        job_id=GET_JOBS[0].job_id,
        pages_number=30,
        status=FileStatusEnumSchema.pending,
    ),
)
JOB_TEST_REVISIONS = (
    {
        "revision": "4a8a9fc31dc15a4b87bb145b05db3ae0bf2333e4",
        "user": JOB_TEST_ANNOTATORS[0].user_id,
        "pipeline": None,
        "date": "2021-10-01 01:01:01.000000",
        "file_id": FILE_TEST_IDS[0],
        "job_id": JOB_TEST_IDS[0],
        "pages": {"1": "3459cdd930c2ceaa94497601f8094479fe6d56ff"},
        "validated": [],
        "tenant": JOB_TEST_TENANTS[0],
        "failed_validation_pages": [],
    },
    {
        "revision": "19e6c13f693d434d250e875715d00553f0a825e1",
        "user": JOB_TEST_ANNOTATORS[1].user_id,
        "pipeline": None,
        "date": "2021-10-01 01:02:01.000000",
        "file_id": FILE_TEST_IDS[0],
        "job_id": JOB_TEST_IDS[1],
        "pages": {"1": "3caab4598f4263cb58557bd440e4bca94fe3a311"},
        "validated": [],
        "tenant": JOB_TEST_TENANTS[0],
        "failed_validation_pages": [],
    },
    {
        "revision": "7685002fe74502e2fbb56fd3a5c493131cef2b2d",
        "user": None,
        "pipeline": PIPELINE_ID,
        "date": "2021-10-01 01:03:01.000000",
        "file_id": FILE_TEST_IDS[0],
        "job_id": JOB_TEST_IDS[3],
        "pages": {"1": "8eca159eee1ea384dedfbdeb092811ac6bf35ba0"},
        "validated": [],
        "tenant": JOB_TEST_TENANTS[0],
        "failed_validation_pages": [],
    },
    {
        "revision": "bbda2529d514ef45ce04bcf2eb8d31664e16bfb7",
        "user": JOB_TEST_ANNOTATORS[2].user_id,
        "pipeline": None,
        "date": "2021-10-01 01:04:01.000000",
        "file_id": FILE_TEST_IDS[1],
        "job_id": JOB_TEST_IDS[2],
        "pages": {"1": "1db28332a39c9b7f213081933bd0a1b946fd09d1"},
        "validated": [],
        "tenant": JOB_TEST_TENANTS[0],
        "failed_validation_pages": [],
    },
    {
        "revision": "b384d3212bb8557f68d3f51f00f0ca89e0960bf3",
        "user": None,
        "pipeline": PIPELINE_ID,
        "date": "2021-10-01 01:05:01.000000",
        "file_id": FILE_TEST_IDS[0],
        "job_id": JOB_TEST_IDS[4],
        "pages": {"1": "f4554dfa3ff5b0dd21becacc48ba381b8962e1e0"},
        "validated": [],
        "tenant": JOB_TEST_TENANTS[1],
        "failed_validation_pages": [],
    },
)

MISSING_FILE_ID = 100


@pytest.mark.integration
@patch.object(Session, "query")
def test_get_jobs_by_file_id_sql_connection_error(
    Session,
    prepare_db_for_get_job,
):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.get(
        f"{ANNOTATION_PATH}/{JOB_TEST_REVISIONS[0]['file_id']}",
        headers={
            HEADER_TENANT: JOB_TEST_TENANTS[0],
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 500
    assert "Error: " in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["file_id", "tenant"],
    [
        (MISSING_FILE_ID, JOB_TEST_TENANTS[0]),
        (FILE_TEST_IDS[0], JOB_TEST_TENANTS[1]),
    ],
)
def test_get_jobs_by_file_id_404_error(
    prepare_db_for_get_job, tenant, file_id
):
    response = client.get(
        f"{ANNOTATION_PATH}/{file_id}",
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 404
    assert f"File with file_id {file_id} wasn't found" in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["file_id", "tenant", "expected_response"],
    [
        (
            FILE_TEST_IDS[0],
            JOB_TEST_TENANTS[0],
            [
                {
                    "is_manual": True,
                    "job_id": 1,
                },
                {
                    "is_manual": True,
                    "job_id": 2,
                },
                {
                    "is_manual": False,
                    "job_id": 4,
                },
            ],
        ),
        (
            FILE_TEST_IDS[1],
            JOB_TEST_TENANTS[0],
            [
                {
                    "is_manual": True,
                    "job_id": 3,
                }
            ],
        ),
    ],
)
def test_get_jobs_by_file(
    prepare_db_for_get_job, file_id, tenant, expected_response
):
    response = client.get(
        f"{ANNOTATION_PATH}/{file_id}",
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.integration
def test_get_jobs_name(monkeypatch, prepare_db_for_get_job):
    session = prepare_db_for_get_job
    job_ids = [1, 2, 3]
    monkeypatch.setattr(
        "annotation.jobs.services.get_job_names",
        Mock(return_value={3: "JobNameFromJobsMicroservice"}),
    )
    expected_result = {
        1: "Job1name",
        2: "Job2name",
        3: "JobNameFromJobsMicroservice",
    }
    result = collect_job_names(
        session, job_ids, JOB_TEST_TENANTS[0], TEST_TOKEN
    )
    job_name_from_db = session.query(Job.name).filter(Job.job_id == 3).scalar()
    assert job_name_from_db == "JobNameFromJobsMicroservice"
    assert result == expected_result
