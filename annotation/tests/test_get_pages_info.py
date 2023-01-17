from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.annotations import accumulate_pages_info
from app.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from app.models import AnnotatedDoc, File, Job, ManualAnnotationTask, User
from app.schemas import TaskStatusEnumSchema, ValidationSchema
from app.tasks import get_task_revisions
from tests.consts import CRUD_TASKS_PATH
from tests.override_app_dependency import TEST_TENANT, TEST_TOKEN, app

client = TestClient(app)

NOT_EXISTING_TENANT = "not-exist"
ANNOTATOR = User(
    user_id="110250e5-f1a8-4610-beeb-1956fc804f43",
)
FILE = File(file_id=1, tenant=TEST_TENANT, job_id=1, pages_number=10)
JOB = Job(
    job_id=1,
    callback_url="http://www.test.com/test1",
    annotators=[ANNOTATOR],
    is_auto_distribution=False,
    files=[FILE],
    deadline=None,
    tenant=TEST_TENANT,
    validation_type=ValidationSchema.cross,
)

TASKS = (
    ManualAnnotationTask(
        id=1,
        file_id=FILE.file_id,
        pages=[1, 2, 3, 4, 5, 6],
        job_id=JOB.job_id,
        user_id=ANNOTATOR.user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.in_progress,
        deadline=None,
    ),
    ManualAnnotationTask(
        id=2,
        file_id=FILE.file_id,
        pages=[1, 2, 3],
        job_id=JOB.job_id,
        user_id=ANNOTATOR.user_id,
        is_validation=False,
        status=TaskStatusEnumSchema.in_progress,
        deadline=None,
    ),
)
ANNOTATED_DOCS = [
    AnnotatedDoc(
        revision="1",
        user=ANNOTATOR.user_id,
        pipeline=None,
        date="2004-10-19 10:23:54",
        file_id=FILE.file_id,
        job_id=JOB.job_id,
        pages={},
        validated=[1, 2],
        failed_validation_pages=[3, 4],
        tenant=TEST_TENANT,
        task_id=TASKS[0].id,
    ),
    AnnotatedDoc(
        revision="2",
        user=ANNOTATOR.user_id,
        pipeline=None,
        date="2004-10-19 10:23:55",
        file_id=FILE.file_id,
        job_id=JOB.job_id,
        pages={},
        validated=[3],
        failed_validation_pages=[2],
        tenant=TEST_TENANT,
        task_id=TASKS[0].id,
    ),
]
PAGES_INFO_ENTITIES = [FILE, JOB, *TASKS, *ANNOTATED_DOCS]

DOCS_FOR_ACCUMULATE_PAGES_INFO = [
    [
        AnnotatedDoc(
            revision="1",
            user=ANNOTATOR.user_id,
            pipeline=None,
            date="2004-10-19 10:23:54",
            file_id=FILE.file_id,
            job_id=JOB.job_id,
            pages={},
            validated=[1, 2],
            failed_validation_pages=[3, 4],
            tenant=TEST_TENANT,
            task_id=TASKS[0].id,
        ),
        AnnotatedDoc(
            revision="2",
            user=ANNOTATOR.user_id,
            pipeline=None,
            date="2004-10-19 10:23:55",
            file_id=FILE.file_id,
            job_id=JOB.job_id,
            pages={},
            validated=[],
            failed_validation_pages=[],
            tenant=TEST_TENANT,
            task_id=TASKS[0].id,
        ),
    ],
    [
        AnnotatedDoc(
            revision="1",
            user=ANNOTATOR.user_id,
            pipeline=None,
            date="2004-10-19 10:23:54",
            file_id=FILE.file_id,
            job_id=JOB.job_id,
            pages={},
            validated=[],
            failed_validation_pages=[],
            tenant=TEST_TENANT,
            task_id=TASKS[0].id,
        ),
        AnnotatedDoc(
            revision="2",
            user=ANNOTATOR.user_id,
            pipeline=None,
            date="2004-10-19 10:23:55",
            file_id=FILE.file_id,
            job_id=JOB.job_id,
            pages={},
            validated=[1, 2],
            failed_validation_pages=[3, 4],
            tenant=TEST_TENANT,
            task_id=TASKS[0].id,
        ),
    ],
    [
        AnnotatedDoc(
            revision="1",
            user=ANNOTATOR.user_id,
            pipeline=None,
            date="2004-10-19 10:23:54",
            file_id=FILE.file_id,
            job_id=JOB.job_id,
            pages={"1": "1"},
            validated=[],
            failed_validation_pages=[],
            tenant=TEST_TENANT,
            task_id=TASKS[0].id,
        ),
    ],
]

EXPECTED_ACCUMULATE_PAGES_INFO = ({1, 3}, {4, 2}, set(), {5, 6})


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["revisions", "task_pages", "expected_result"],
    [
        (ANNOTATED_DOCS, (TASKS[0].pages,), EXPECTED_ACCUMULATE_PAGES_INFO),
        (
            DOCS_FOR_ACCUMULATE_PAGES_INFO[0],
            (TASKS[0].pages,),
            ({1, 2}, {3, 4}, set(), {5, 6}),
        ),
        (
            DOCS_FOR_ACCUMULATE_PAGES_INFO[1],
            (TASKS[0].pages,),
            ({1, 2}, {3, 4}, set(), {5, 6}),
        ),
        (
            DOCS_FOR_ACCUMULATE_PAGES_INFO[2],
            (TASKS[0].pages,),
            (set(), set(), {1}, {2, 3, 4, 5, 6}),
        ),
    ],
)
def test_accumulate_pages_info(revisions, task_pages, expected_result):
    validated, failed, annotated, not_processed, _ = accumulate_pages_info(
        *task_pages, revisions
    )
    assert (validated, failed, annotated, not_processed) == expected_result


@pytest.mark.integration
@pytest.mark.parametrize(
    [
        "tenant",
        "job_id",
        "task_id",
        "file_id",
        "task_pages",
        "expected_result",
    ],
    [
        (
            TEST_TENANT,
            TASKS[0].job_id,
            TASKS[0].id,
            TASKS[0].file_id,
            TASKS[0].pages,
            ANNOTATED_DOCS,
        ),
        (
            TEST_TENANT,
            TASKS[0].job_id,
            100,
            TASKS[0].file_id,
            TASKS[0].pages,
            [],
        ),
        (
            NOT_EXISTING_TENANT,
            TASKS[0].job_id,
            TASKS[0].id,
            TASKS[0].file_id,
            TASKS[0].pages,
            [],
        ),
    ],
)
def test_get_task_revisions(
    db_get_pages_info,
    tenant,
    job_id,
    task_id,
    file_id,
    task_pages,
    expected_result,
):
    actual_result = get_task_revisions(
        db_get_pages_info, tenant, job_id, task_id, file_id, task_pages
    )
    assert actual_result == expected_result


@pytest.mark.integration
@pytest.mark.parametrize(
    ["task_id", "tenant", "expected_code", "expected_response"],
    [
        (
            ANNOTATED_DOCS[0].task_id,
            TEST_TENANT,
            200,
            {
                "annotated_pages": [],
                "failed_validation_pages": [2, 4],
                "validated": [1, 3],
                "not_processed": [5, 6],
            },
        ),
        (
            3,
            TEST_TENANT,
            404,
            {"detail": "Task 3 wasn't found."},
        ),
        (
            TASKS[1].id,
            TEST_TENANT,
            200,
            {
                "annotated_pages": [],
                "failed_validation_pages": [],
                "validated": [],
                "not_processed": TASKS[1].pages,
            },
        ),
    ],
)
def test_get_pages_info_status_codes(
    db_get_pages_info,
    task_id,
    tenant,
    expected_code,
    expected_response,
):
    response = client.get(
        CRUD_TASKS_PATH + f"/{task_id}/pages_summary",
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == expected_code
    assert response.json() == expected_response


@pytest.mark.integration
@patch.object(Session, "query")
def test_get_pages_info_sql_connection_error(
    Session,
    db_get_pages_info,
    task_id=ANNOTATED_DOCS[0].task_id,
    tenant=TEST_TENANT,
):
    Session.side_effect = Mock(side_effect=SQLAlchemyError())
    response = client.get(
        CRUD_TASKS_PATH + f"/{task_id}/pages_summary",
        headers={
            HEADER_TENANT: tenant,
            AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
        },
    )
    assert response.status_code == 500
    assert "Error: connection error" in response.text
