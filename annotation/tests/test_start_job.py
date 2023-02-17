from unittest.mock import Mock, patch

import pytest
import responses
from fastapi.testclient import TestClient
from requests.exceptions import RequestException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from annotation.annotations import row_to_dict
from annotation.jobs import update_inner_job_status
from annotation.models import Category, File, Job, ManualAnnotationTask, User
from annotation.schemas import (
    CategoryTypeSchema,
    JobStatusEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app

client = TestClient(app)

START_JOB_PATH = "/jobs/{job_id}/start"
CATEGORIES = [
    Category(
        id="aeacb631672e4b048b42ed76f0ede2c5",
        name="Test",
        type=CategoryTypeSchema.box,
    ),
]
ANNOTATORS = (
    User(user_id="aeacb631-672e-4b04-8b42-ed76f0ede2c5"),
    User(user_id="a332f24d-e063-4bd2-9475-a503bc2eb3ad"),
    User(user_id="fe208415-f371-4abe-8ea8-bcc8841b0ec6"),
)
VALIDATION_TYPE = "cross"
CHANGE_STATUSES_JOBS = (
    Job(
        job_id=1,
        is_auto_distribution=False,
        categories=CATEGORIES,
        callback_url="http://www.test.com",
        annotators=[ANNOTATORS[0], ANNOTATORS[1], ANNOTATORS[2]],
        validators=[ANNOTATORS[0], ANNOTATORS[1], ANNOTATORS[2]],
        validation_type=ValidationSchema.hierarchical,
        deadline=None,
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=2,
        is_auto_distribution=False,
        categories=CATEGORIES,
        callback_url="http://www.test.com",
        annotators=[ANNOTATORS[2]],
        validators=[ANNOTATORS[2]],
        validation_type=ValidationSchema.hierarchical,
        deadline=None,
        tenant=TEST_TENANT,
    ),
    Job(
        job_id=3,
        is_auto_distribution=False,
        categories=CATEGORIES,
        callback_url="http://www.test.com",
        annotators=[ANNOTATORS[2]],
        validators=[ANNOTATORS[2]],
        validation_type=ValidationSchema.hierarchical,
        deadline=None,
        tenant=TEST_TENANT,
    ),
)
FILES = (
    File(
        file_id=1,
        tenant=TEST_TENANT,
        job_id=CHANGE_STATUSES_JOBS[0].job_id,
        pages_number=100,
    ),
    File(
        file_id=2,
        tenant=TEST_TENANT,
        job_id=CHANGE_STATUSES_JOBS[0].job_id,
        pages_number=100,
    ),
    File(
        file_id=3,
        tenant=TEST_TENANT,
        job_id=CHANGE_STATUSES_JOBS[0].job_id,
        pages_number=100,
    ),
    File(
        file_id=4,
        tenant=TEST_TENANT,
        job_id=CHANGE_STATUSES_JOBS[1].job_id,
        pages_number=100,
    ),
)
CHANGE_STATUSES_TASKS = [
    ManualAnnotationTask(
        id=1,
        file_id=FILES[0].file_id,
        is_validation=False,
        job_id=CHANGE_STATUSES_JOBS[0].job_id,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        status="Pending",
        user_id=ANNOTATORS[0].user_id,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=2,
        file_id=FILES[1].file_id,
        is_validation=False,
        job_id=CHANGE_STATUSES_JOBS[0].job_id,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        status="Pending",
        user_id=ANNOTATORS[1].user_id,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=3,
        file_id=FILES[2].file_id,
        is_validation=False,
        job_id=CHANGE_STATUSES_JOBS[0].job_id,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        status="Pending",
        user_id=ANNOTATORS[2].user_id,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=4,
        file_id=FILES[0].file_id,
        is_validation=True,
        job_id=CHANGE_STATUSES_JOBS[0].job_id,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        status="Pending",
        user_id=ANNOTATORS[0].user_id,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=5,
        file_id=FILES[1].file_id,
        is_validation=True,
        job_id=CHANGE_STATUSES_JOBS[0].job_id,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        status="Pending",
        user_id=ANNOTATORS[1].user_id,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=6,
        file_id=FILES[2].file_id,
        is_validation=True,
        job_id=CHANGE_STATUSES_JOBS[0].job_id,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        status="Pending",
        user_id=ANNOTATORS[2].user_id,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=7,
        file_id=FILES[3].file_id,
        is_validation=False,
        job_id=CHANGE_STATUSES_JOBS[1].job_id,
        pages=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        status="Pending",
        user_id=ANNOTATORS[2].user_id,
        deadline=None,
    ),
]
MISSING_JOB_ID = 6
JOB_WITHOUT_TASKS = CHANGE_STATUSES_JOBS[2].job_id


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_id", "status"],
    [
        (CHANGE_STATUSES_JOBS[0].job_id, JobStatusEnumSchema.in_progress),
        (CHANGE_STATUSES_JOBS[0].job_id, JobStatusEnumSchema.finished),
        (CHANGE_STATUSES_JOBS[0].job_id, JobStatusEnumSchema.failed),
    ],
)
def test_update_inner_job_status(job_id, status, prepare_db_for_update_job_status):
    update_inner_job_status(prepare_db_for_update_job_status, job_id, status)
    prepare_db_for_update_job_status.commit()
    db_job = prepare_db_for_update_job_status.query(Job).get(job_id)
    assert db_job.status == status


@pytest.mark.integration
@patch.object(Session, "query")
def test_post_start_job_500_response(
    Session,
    prepare_db_for_change_statuses,
    job_id=CHANGE_STATUSES_TASKS[0].job_id,
):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.post(START_JOB_PATH.format(job_id=job_id), headers=TEST_HEADERS)
    assert response.status_code == 500
    assert "Error: connection error" in response.text


@pytest.mark.integration
def test_post_start_wrong_job_404_response(prepare_db_for_change_statuses):
    response = client.post(
        START_JOB_PATH.format(job_id=MISSING_JOB_ID), headers=TEST_HEADERS
    )
    assert response.status_code == 404
    assert f"Job with job_id ({MISSING_JOB_ID}) not found" in response.text


@pytest.mark.integration
def test_post_start_job_404_response(prepare_db_for_change_statuses):
    response = client.post(
        START_JOB_PATH.format(job_id=JOB_WITHOUT_TASKS), headers=TEST_HEADERS
    )
    assert response.status_code == 404
    assert "Tasks for job_id" in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_response_status", "job_response_body", "expected_response"],
    [
        (400, "", "Error: connection error"),
        (None, RequestException(), "Error: connection error"),
    ],
)
@responses.activate
def test_post_start_job_bad_job_response(
    prepare_db_for_change_statuses,
    job_response_status,
    job_response_body,
    expected_response,
):
    job_id = CHANGE_STATUSES_TASKS[0].job_id
    job = prepare_db_for_change_statuses.query(Job).get(job_id)
    responses.add(
        responses.PUT,
        job.callback_url,
        body=job_response_body,
        status=job_response_status,
        headers=TEST_HEADERS,
    )
    response = client.post(START_JOB_PATH.format(job_id=job_id), headers=TEST_HEADERS)
    assert response.status_code == 500
    assert expected_response in response.text
    saved_tasks = (
        prepare_db_for_change_statuses.query(ManualAnnotationTask)
        .filter_by(job_id=job_id)
        .all()
    )
    for save_task in saved_tasks:
        assert save_task.status == TaskStatusEnumSchema.pending


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_id", "expected_response"],
    [
        (
            1,
            [
                dict(row_to_dict(x), status="Ready")
                if not x.is_validation
                else row_to_dict(x)
                for x in CHANGE_STATUSES_TASKS[:6]
            ],
        ),
        (
            2,
            [
                dict(
                    row_to_dict(CHANGE_STATUSES_TASKS[6]),
                    status="Ready",
                )
            ],
        ),
    ],
)
@responses.activate
def test_post_start_job_tasks_statuses(
    prepare_db_for_change_statuses, job_id, expected_response
):
    job = prepare_db_for_change_statuses.query(Job).get(job_id)
    responses.add(
        responses.PUT,
        job.callback_url,
        status=200,
        headers=TEST_HEADERS,
    )
    response = client.post(START_JOB_PATH.format(job_id=job_id), headers=TEST_HEADERS)
    prepare_db_for_change_statuses.commit()
    assert response.status_code == 200
    assert response.json() == expected_response
    assert job.status == "In Progress"
