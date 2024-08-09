import uuid
from unittest.mock import MagicMock

import pytest

from annotation.errors import FieldConstraintError
from annotation.jobs.services import check_annotators, update_inner_job_status
from annotation.models import Category, File, Job, User
from annotation.schemas import (
    CategoryTypeSchema,
    FileStatusEnumSchema,
    JobStatusEnumSchema,
    ValidationSchema,
)


@pytest.fixture
def job_tenant():
    return "test"


@pytest.fixture
def job_ids():
    return (1, 2, 3)


ANNOTATORS = (
    User(user_id="82533770-a99e-4873-8b23-6bbda86b59ae"),
    User(user_id="ef81a4d0-cc01-447b-9025-a70ed441672d"),
)


@pytest.fixture
def job_annotators():
    return (
        User(user_id="82533770-a99e-4873-8b23-6bbda86b59ae"),
        User(user_id="ef81a4d0-cc01-447b-9025-a70ed441672d"),
    )


@pytest.fixture
def categories():
    return Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    )


@pytest.fixture
def jobs_to_test_progress(annotators, categories):
    return (
        Job(
            job_id=job_ids[0],
            callback_url="http://www.test.com",
            annotators=[annotators[0], annotators[1]],
            validation_type=ValidationSchema.cross,
            is_auto_distribution=False,
            categories=categories,
            deadline="2021-10-19T01:01:01",
            tenant=job_tenant,
        ),
        Job(
            job_id=job_ids[1],
            callback_url="http://www.test.com",
            annotators=[],
            validation_type=ValidationSchema.cross,
            is_auto_distribution=False,
            categories=categories,
            deadline="2021-10-19T01:01:01",
            tenant=job_tenant,
        ),
        Job(
            job_id=job_ids[2],
            callback_url="http://www.test.com",
            annotators=[annotators[0], annotators[1]],
            validation_type=ValidationSchema.cross,
            is_auto_distribution=False,
            categories=categories,
            deadline="2021-10-19T01:01:01",
            tenant=job_tenant,
        ),
    )


@pytest.fixture
def files(jobs_to_test_progress):
    return (
        File(
            file_id=1,
            tenant=job_tenant,
            job_id=jobs_to_test_progress[0].job_id,
            pages_number=5,
            status=FileStatusEnumSchema.pending,
        ),
        File(
            file_id=2,
            tenant=job_tenant,
            job_id=jobs_to_test_progress[1].job_id,
            pages_number=5,
            status=FileStatusEnumSchema.pending,
        ),
        File(
            file_id=3,
            tenant=job_tenant,
            job_id=jobs_to_test_progress[2].job_id,
            pages_number=5,
            status=FileStatusEnumSchema.pending,
        ),
    )


def test_update_inner_job_status(job_ids):
    mock_session = MagicMock()
    update_inner_job_status(
        mock_session, job_ids[0], JobStatusEnumSchema.finished
    )
    mock_session.query(Job).filter(
        Job.job_id == job_ids[0]
    ).update.assert_called_with({"status": JobStatusEnumSchema.finished})


@pytest.mark.parametrize(
    (
        "validation_type",
        "annotators",
    ),
    [
        (ValidationSchema.cross, set((uuid.UUID(ANNOTATORS[0].user_id),))),
        (ValidationSchema.hierarchical, set()),
        (
            ValidationSchema.validation_only,
            set((uuid.UUID(ANNOTATORS[0].user_id),)),
        ),
    ],
)
def test_check_annotators(validation_type, annotators):
    with pytest.raises(FieldConstraintError):
        check_annotators(annotators, validation_type)
