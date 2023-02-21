import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

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
from tests.consts import ANNOTATION_PATH
from tests.override_app_dependency import TEST_TENANT, TEST_TOKEN, app

client = TestClient(app)

DIFF_TENANT = "diff-tenant"
PIPELINE_ID = 10
FILE_ID_1 = 1
FILE_ID_2 = 2
JOB_ID = 1
NOT_EXISTING_TENANT = "not-exist"
NOT_EXISTING_ID = 20
BAD_ID = "uuid"
PART_REV_PATH = ANNOTATION_PATH + "/{job_id}/{file_id}/{revision}"

REV_WITHOUT_ANNOTATION_ANNOTATOR = User(
    user_id="110250e5-f1a8-4610-beeb-1956fc804f43",
)
REV_WITHOUT_ANNOTATION_CATEGORIES = [
    Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    ),
]
REV_WITHOUT_ANNOTATION_FILE = File(
    file_id=1, tenant=TEST_TENANT, job_id=1, pages_number=10
)

REV_WITHOUT_ANNOTATION_JOB = Job(
    job_id=1,
    callback_url="http://www.test.com/test1",
    annotators=[REV_WITHOUT_ANNOTATION_ANNOTATOR],
    files=[REV_WITHOUT_ANNOTATION_FILE],
    is_auto_distribution=False,
    categories=REV_WITHOUT_ANNOTATION_CATEGORIES,
    deadline=None,
    tenant=TEST_TENANT,
    validation_type=ValidationSchema.cross,
)

REV_WITHOUT_ANNOTATION_TASK = ManualAnnotationTask(
    id=1,
    file_id=REV_WITHOUT_ANNOTATION_FILE.file_id,
    pages=[1],
    job_id=REV_WITHOUT_ANNOTATION_JOB.job_id,
    user_id=REV_WITHOUT_ANNOTATION_ANNOTATOR.user_id,
    is_validation=True,
    status=TaskStatusEnumSchema.in_progress,
    deadline=None,
)

REV_WITHOUT_ANNOTATION_DOC_1 = {
    "revision": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
    "user": REV_WITHOUT_ANNOTATION_ANNOTATOR.user_id,
    "pipeline": None,
    "date": "2021-10-01T01:14:01",
    "file_id": FILE_ID_1,
    "job_id": JOB_ID,
    "pages": {
        "1": "adda414648714f01c1c9657646b72ebb4433c8b5",
        "2": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
    },
    "validated": [3],
    "tenant": TEST_TENANT,
    "task_id": REV_WITHOUT_ANNOTATION_TASK.id,
    "failed_validation_pages": [],
    "links_json": [],
}
REV_WITHOUT_ANNOTATION_DOC_2 = {
    "revision": "20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
    "user": None,
    "pipeline": PIPELINE_ID,
    "date": "2021-10-02T01:14:01",
    "file_id": FILE_ID_1,
    "job_id": JOB_ID,
    "pages": {},
    "validated": [1, 3],
    "tenant": TEST_TENANT,
    "task_id": None,
    "failed_validation_pages": [],
    "links_json": [],
}
REV_WITHOUT_ANNOTATION_DOC_3 = {
    "revision": "20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
    "user": None,
    "pipeline": PIPELINE_ID,
    "date": "2021-10-02T01:14:01",
    "file_id": FILE_ID_2,
    "job_id": JOB_ID,
    "pages": {},
    "validated": [1, 3],
    "tenant": DIFF_TENANT,
    "task_id": None,
    "failed_validation_pages": [],
    "links_json": [],
}
REV_WITHOUT_ANNOTATION_RESPONSE = [
    {
        **REV_WITHOUT_ANNOTATION_DOC_1,
        "similar_revisions": None,
        "categories": [],
    },
    {
        **REV_WITHOUT_ANNOTATION_DOC_2,
        "similar_revisions": None,
        "categories": [],
    },
]


def construct_rev_without_annotation_path(job_id: int, file_id: int) -> str:
    return f"/revisions/{job_id}/{file_id}"


@pytest.mark.integration
@pytest.mark.parametrize(
    ["file_id", "tenant", "expected_code", "expected_response"],
    [
        (
            FILE_ID_1,
            TEST_TENANT,
            200,
            REV_WITHOUT_ANNOTATION_RESPONSE,
        ),  # get list of two revisions
        (
            FILE_ID_2,
            DIFF_TENANT,
            200,
            [
                {
                    **REV_WITHOUT_ANNOTATION_DOC_3,
                    "similar_revisions": None,
                    "categories": [],
                }
            ],
        ),  # get list of one revision
        (
            NOT_EXISTING_ID,
            TEST_TENANT,
            200,
            [],
        ),  # revision with such file id does not exist
        (
            FILE_ID_1,
            NOT_EXISTING_TENANT,
            200,
            [],
        ),  # given tenant does not match with revision`s
        (
            BAD_ID,
            NOT_EXISTING_TENANT,
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "file_id"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
    ],
)
def test_get_revisions_without_annotation_status_codes(
    db_revisions_without_annotation,
    file_id,
    tenant,
    expected_code,
    expected_response,
):
    response = client.get(
        construct_rev_without_annotation_path(JOB_ID, file_id),
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )

    assert response.status_code == expected_code
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
def test_get_revisions_without_annotation_db_exceptions(
    monkeypatch, db_errors
):
    response = client.get(
        construct_rev_without_annotation_path(JOB_ID, FILE_ID_1),
        headers={"X-Current-Tenant": TEST_TENANT},
    )
    assert response.status_code == 500
