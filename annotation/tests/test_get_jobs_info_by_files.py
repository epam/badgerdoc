from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from annotation.jobs.services import get_jobs_by_files
from annotation.models import File, Job, User
from annotation.schemas import JobStatusEnumSchema, ValidationSchema
from tests.consts import POST_JOBS_PATH
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app

client = TestClient(app)


ANNOTATORS = [
    User(
        user_id=f"{i}10250e5-f1a8-4610-beeb-1956fc804f43",
    )
    for i in range(1, 7)
]
ANOTHER_TENANT = "another_tenant"
FILES_FIRST_JOB = [
    File(file_id=1, tenant=TEST_TENANT, job_id=1, pages_number=5),
    File(file_id=2, tenant=TEST_TENANT, job_id=1, pages_number=5),
    File(file_id=3, tenant=TEST_TENANT, job_id=1, pages_number=5),
    File(file_id=6, tenant=ANOTHER_TENANT, job_id=1, pages_number=5),
]
FILES_SECOND_JOB = [
    File(file_id=3, tenant=TEST_TENANT, job_id=2, pages_number=5),
    File(file_id=4, tenant=TEST_TENANT, job_id=2, pages_number=5),
]
FILES_THIRD_JOB = [File(file_id=5, tenant=TEST_TENANT, job_id=3, pages_number=5)]

JOBS = [
    # files with ids [1, 2, 3, 6] belong to this job
    Job(
        job_id=1,
        callback_url="http://www.test.com/test1",
        annotators=ANNOTATORS[:2],
        is_auto_distribution=False,
        files=FILES_FIRST_JOB,
        tenant=TEST_TENANT,
        validation_type=ValidationSchema.cross,
        status=JobStatusEnumSchema.pending,
    ),
    # files with ids [3, 4] belong to this job
    Job(
        job_id=2,
        callback_url="http://www.test.com/test1",
        annotators=ANNOTATORS[2:4],
        is_auto_distribution=False,
        files=FILES_SECOND_JOB,
        tenant=TEST_TENANT,
        validation_type=ValidationSchema.cross,
        status=JobStatusEnumSchema.in_progress,
    ),
    # file with id [5] belongs to this job,
    # this job has different tenant
    Job(
        job_id=3,
        callback_url="http://www.test.com/test1",
        annotators=ANNOTATORS[4:],
        is_auto_distribution=False,
        files=FILES_THIRD_JOB,
        tenant=ANOTHER_TENANT,
        validation_type=ValidationSchema.cross,
        status=JobStatusEnumSchema.pending,
    ),
]

JOB_NAMES = {
    # for jobs with ids [2, 3] names are not present
    1: "first_job_name"
}


@pytest.mark.integration
@pytest.mark.parametrize(
    ["file_ids", "expected_result"],
    [
        # file with id = 1 participates only in job with id = 1
        # job with id = 1 has name "first_job_name" and status = Pending
        (
            {1},
            {
                1: [
                    {
                        "id": JOBS[0].job_id,
                        "name": "first_job_name",
                        "status": JOBS[0].status,
                    }
                ]
            },
        ),
        # file with id = 4 participates only in job with id = 2
        # job with id = 2 does not have name and has status = In Progress
        (
            {4},
            {
                4: [
                    {
                        "id": JOBS[1].job_id,
                        "name": None,
                        "status": JOBS[1].status,
                    }
                ]
            },
        ),
        # file with id = 3 participates in jobs with ids [1, 2]
        # job with id = 1 has name "first_job_name" and status = Pending
        # job with id = 2 does not have name and has status = In Progress
        # jobs are sorted in desc order by job_id
        (
            {3},
            {
                3: [
                    {
                        "id": JOBS[1].job_id,
                        "name": None,
                        "status": JOBS[1].status,
                    },
                    {
                        "id": JOBS[0].job_id,
                        "name": "first_job_name",
                        "status": JOBS[0].status,
                    },
                ]
            },
        ),
        # file with id = 5 participates only in job with id = 3,
        # but jobs tenant is different
        # empty dict should be returned
        (
            {5},
            {},
        ),
        # if file does not exist, empty dict should be returned
        (
            {1000},
            {},
        ),
        # file with id = 6 participates only in job with id = 1,
        # but files tenant is different
        # empty list should be returned
        (
            {6},
            {},
        ),
        # files with ids [1, 2] participate only in job with id = 1
        # job with id = 1 has name "first_job_name" and status = Pending
        (
            {1, 2},
            {
                1: [
                    {
                        "id": JOBS[0].job_id,
                        "name": "first_job_name",
                        "status": JOBS[0].status,
                    }
                ],
                2: [
                    {
                        "id": JOBS[0].job_id,
                        "name": "first_job_name",
                        "status": JOBS[0].status,
                    }
                ],
            },
        ),
        # file with id = 3 participates in jobs with ids [1, 2]
        # job with id = 1 has name "first_job_name" and status = Pending
        # job with id = 2 does not have name and has status = In Progress
        # file with id = 1000 does not exist, it will not be present
        # in dict
        # jobs are sorted in desc order by job_id
        (
            {3, 1000},
            {
                3: [
                    {
                        "id": JOBS[1].job_id,
                        "name": None,
                        "status": JOBS[1].status,
                    },
                    {
                        "id": JOBS[0].job_id,
                        "name": "first_job_name",
                        "status": JOBS[0].status,
                    },
                ],
            },
        ),
        # file with id = 5 participates only in job with id = 3,
        # but jobs tenant is different
        # file with id = 6 participates only in job with id = 1,
        # but files tenant is different
        # empty dict should be returned
        (
            {5, 6},
            {},
        ),
    ],
)
def test_get_jobs_by_file(
    monkeypatch, db_get_jobs_info_by_files, file_ids, expected_result
):
    db = db_get_jobs_info_by_files
    monkeypatch.setattr(
        "annotation.jobs.services.get_job_names",
        Mock(return_value=JOB_NAMES),
    )

    actual_result = dict(get_jobs_by_files(db, file_ids, TEST_TENANT, "token"))

    assert actual_result == expected_result


@pytest.mark.integration
@pytest.mark.parametrize(
    ["file_ids", "expected_result"],
    [
        # files with ids [1, 2] participate only in job with id = 1
        # job with id = 1 has name "first_job_name" and status = Pending
        (
            {1, 2},
            {
                "1": [
                    {
                        "id": JOBS[0].job_id,
                        "name": "first_job_name",
                        "status": JOBS[0].status,
                    }
                ],
                "2": [
                    {
                        "id": JOBS[0].job_id,
                        "name": "first_job_name",
                        "status": JOBS[0].status,
                    }
                ],
            },
        ),
        # file with id = 3 participates in jobs with ids [1, 2]
        # job with id = 1 has name "first_job_name" and status = Pending
        # job with id = 2 does not have name and has status = In Progress
        # file with id = 1000 does not exist, for this file empty list
        # should be returned
        # jobs are sorted in desc order by job_id
        (
            {3, 1000},
            {
                "3": [
                    {
                        "id": JOBS[1].job_id,
                        "name": None,
                        "status": JOBS[1].status,
                    },
                    {
                        "id": JOBS[0].job_id,
                        "name": "first_job_name",
                        "status": JOBS[0].status,
                    },
                ],
                "1000": [],
            },
        ),
        # file with id = 5 participates only in job with id = 3,
        # but jobs tenant is different
        # empty list should be returned
        # file with id = 6 participates only in job with id = 1,
        # but files tenant is different
        # empty list should be returned
        (
            {5, 6},
            {
                "5": [],
                "6": [],
            },
        ),
    ],
)
def test_get_jobs_info_by_files(
    monkeypatch, db_get_jobs_info_by_files, file_ids, expected_result
):
    monkeypatch.setattr(
        "annotation.jobs.services.get_job_names",
        Mock(return_value=JOB_NAMES),
    )
    response = client.get(
        "/jobs",
        headers=TEST_HEADERS,
        params={"file_ids": file_ids},
    )
    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["db_errors"],
    [
        (DBAPIError,),
        (SQLAlchemyError,),
    ],
    indirect=["db_errors"],
)
def test_get_jobs_info_by_files_db_errors(db_errors, monkeypatch):
    monkeypatch.setattr(
        "annotation.jobs.services.get_job_names",
        Mock(return_value=JOB_NAMES),
    )

    response = client.get(
        POST_JOBS_PATH,
        headers=TEST_HEADERS,
        params={"file_ids": {1, 2}},
    )
    assert response.status_code == 500
