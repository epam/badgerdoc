import pytest
from fastapi.testclient import TestClient

from app.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from app.models import Category, File, Job, User
from app.schemas import (
    CategoryTypeSchema,
    FileStatusEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from tests.consts import POST_JOBS_PATH
from tests.override_app_dependency import TEST_TOKEN, app

client = TestClient(app)

JOB_TENANT = "test"
JOB_TEST_PROGRESS_ANNOTATORS = (
    User(user_id="82533770-a99e-4873-8b23-6bbda86b59ae"),
    User(user_id="ef81a4d0-cc01-447b-9025-a70ed441672d"),
)
CATEGORIES = [
    Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    )
]

JOB_IDS = [1, 2, 3]
JOBS_TO_TEST_PROGRESS = (
    Job(  # Annotation job with 3 tasks in progress, 1 finished task
        job_id=JOB_IDS[0],
        callback_url="http://www.test.com",
        annotators=[
            JOB_TEST_PROGRESS_ANNOTATORS[0],
            JOB_TEST_PROGRESS_ANNOTATORS[1],
        ],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=JOB_TENANT,
    ),
    Job(  # Extraction job with no tasks
        job_id=JOB_IDS[1],
        callback_url="http://www.test.com",
        annotators=[],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=JOB_TENANT,
    ),
    Job(  # Job with all tasks in progress
        job_id=JOB_IDS[2],
        callback_url="http://www.test.com",
        annotators=[
            JOB_TEST_PROGRESS_ANNOTATORS[0],
            JOB_TEST_PROGRESS_ANNOTATORS[1],
        ],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=JOB_TENANT,
    ),
)
FILE_TEST_PROGRESS = File(
    file_id=1,
    tenant=JOB_TENANT,
    job_id=JOB_IDS[0],
    pages_number=5,
    status=FileStatusEnumSchema.pending,
)
FILE_TEST_PROGRESS_2 = File(
    file_id=2,
    tenant=JOB_TENANT,
    job_id=JOB_IDS[1],
    pages_number=5,
    status=FileStatusEnumSchema.pending,
)
FILE_TEST_PROGRESS_3 = File(
    file_id=3,
    tenant=JOB_TENANT,
    job_id=JOB_IDS[2],
    pages_number=5,
    status=FileStatusEnumSchema.pending,
)
TASKS_TEST_PROGRESS = (
    {  # finished task
        "id": 1,
        "file_id": FILE_TEST_PROGRESS.file_id,
        "pages": [1, 2],
        "job_id": JOB_IDS[0],
        "user_id": JOB_TEST_PROGRESS_ANNOTATORS[0].user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.finished,
        "deadline": None,
    },
    {  # task in ready status
        "id": 2,
        "file_id": FILE_TEST_PROGRESS.file_id,
        "pages": [3, 4],
        "job_id": JOB_IDS[0],
        "user_id": JOB_TEST_PROGRESS_ANNOTATORS[0].user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.ready,
        "deadline": None,
    },
    {  # task with in_progress status
        "id": 3,
        "file_id": FILE_TEST_PROGRESS.file_id,
        "pages": [5],
        "job_id": JOB_IDS[0],
        "user_id": JOB_TEST_PROGRESS_ANNOTATORS[1].user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    },
    {  # task with in_progress status
        "id": 4,
        "file_id": FILE_TEST_PROGRESS_3.file_id,
        "pages": [1, 2, 3],
        "job_id": JOB_IDS[2],
        "user_id": JOB_TEST_PROGRESS_ANNOTATORS[1].user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    },
    {  # task with in_progress status
        "id": 5,
        "file_id": FILE_TEST_PROGRESS_3.file_id,
        "pages": [4, 5],
        "job_id": JOB_IDS[2],
        "user_id": JOB_TEST_PROGRESS_ANNOTATORS[1].user_id,
        "is_validation": False,
        "status": TaskStatusEnumSchema.in_progress,
        "deadline": None,
    },
)


@pytest.mark.integration
@pytest.mark.parametrize(
    ["job_id", "tenant", "expected_progress"],
    [
        (JOB_IDS[0], JOB_TENANT, '{"finished":1,"total":3}'),
        (JOB_IDS[1], JOB_TENANT, '{"finished":0,"total":0}'),
        (JOB_IDS[2], JOB_TENANT, '{"finished":0,"total":2}'),
    ],
)
def test_get_jobs_progress(
    prepare_db_for_get_job_progress, job_id, tenant, expected_progress
):
    response = client.get(
        f"{POST_JOBS_PATH}/{job_id}/progress",
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 200
    assert expected_progress in response.text
