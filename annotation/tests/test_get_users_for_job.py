import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from annotation.models import Job, User
from annotation.schemas import ValidationSchema
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app

client = TestClient(app)

USERS_FOR_JOB_PATH = "/jobs/{job_id}/users"
BAD_ID = "bad"
JOB_ID = "4"

USERS_FOR_JOB_ANNOTATORS = [
    User(user_id="48a2a491-c8f0-4b19-851e-84bf5c326a16", overall_load=35),
    User(user_id="875db618-6624-4025-817f-a69f66ae8bae", overall_load=97),
    User(user_id="6d3140ea-e195-4a60-9407-39ead106e118", overall_load=0),
]
USERS_FOR_JOB_JOBS = [
    Job(
        job_id=4,
        callback_url="http://www.test.com/test1",
        annotators=[USERS_FOR_JOB_ANNOTATORS[0], USERS_FOR_JOB_ANNOTATORS[1]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        deadline=None,
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=5,
        callback_url="http://www.test.com/test1",
        annotators=[USERS_FOR_JOB_ANNOTATORS[2]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        deadline=None,
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=6,
        callback_url="http://www.test.com/test1",
        is_auto_distribution=False,
        validation_type=ValidationSchema.cross,
        deadline=None,
        tenant=TEST_TENANT,
    ),
]
WRONG_JOB_ID = 100


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_id", "expected_status_code", "expected_response"],
    [
        (
            USERS_FOR_JOB_JOBS[0].job_id,
            200,
            [
                {
                    "id": USERS_FOR_JOB_ANNOTATORS[0].user_id,
                    "overall_load": 35,
                },
                {
                    "id": USERS_FOR_JOB_ANNOTATORS[1].user_id,
                    "overall_load": 97,
                },
            ],
        ),
        (
            USERS_FOR_JOB_JOBS[1].job_id,
            200,
            [{"id": USERS_FOR_JOB_ANNOTATORS[2].user_id, "overall_load": 0}],
        ),
        (
            USERS_FOR_JOB_JOBS[2].job_id,
            200,
            [],
        ),
        (
            BAD_ID,
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "job_id"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
    ],
)
def test_get_users_for_job(
    db_get_users_for_job, job_id, expected_status_code, expected_response
):
    response = client.get(
        USERS_FOR_JOB_PATH.format(job_id=job_id), headers=TEST_HEADERS
    )
    assert response.status_code == expected_status_code
    assert response.json() == expected_response


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["db_errors"],
    [
        (DBAPIError,),
        (SQLAlchemyError,),
    ],
    indirect=["db_errors"],
)
def test_get_users_for_job_exceptions(monkeypatch, db_errors):
    response = client.get(
        USERS_FOR_JOB_PATH.format(job_id=JOB_ID), headers=TEST_HEADERS
    )
    assert response.status_code == 500


@pytest.mark.integration
def test_get_users_for_job_404_error(db_get_users_for_job):
    response = client.get(
        USERS_FOR_JOB_PATH.format(job_id=WRONG_JOB_ID), headers=TEST_HEADERS
    )
    assert response.status_code == 404
    assert f"Job with job_id ({WRONG_JOB_ID}) not found" in response.text
