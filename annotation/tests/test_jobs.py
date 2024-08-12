import uuid
from typing import Set, Tuple
from unittest.mock import MagicMock
from uuid import UUID

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
def job_annotators():
    yield (
        User(user_id="82533770-a99e-4873-8b23-6bbda86b59ae"),
        User(user_id="ef81a4d0-cc01-447b-9025-a70ed441672d"),
    )


@pytest.fixture
def categories():
    yield Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    )


@pytest.fixture
def jobs_to_test_progress(job_annotators: Tuple[User], categories: Category):
    yield Job(
        job_id=1,
        callback_url="http://www.test.com",
        annotators=[job_annotators[0], job_annotators[1]],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=categories,
        deadline="2021-10-19T01:01:01",
        tenant="test",
    )


@pytest.fixture
def files(jobs_to_test_progress: Job):
    yield File(
        file_id=1,
        tenant="test",
        job_id=jobs_to_test_progress[0].job_id,
        pages_number=5,
        status=FileStatusEnumSchema.pending,
    )


def test_update_inner_job_status():
    mock_session = MagicMock()
    update_inner_job_status(mock_session, 1, JobStatusEnumSchema.finished)
    mock_session.query(Job).filter(Job.job_id == 1).update.assert_called_with(
        {"status": JobStatusEnumSchema.finished}
    )


@pytest.mark.parametrize(
    (
        "validation_type",
        "annotators",
    ),
    (
        (
            ValidationSchema.cross,
            {uuid.UUID("82533770-a99e-4873-8b23-6bbda86b59ae")},
        ),
        (ValidationSchema.hierarchical, set()),
        (
            ValidationSchema.validation_only,
            {uuid.UUID("82533770-a99e-4873-8b23-6bbda86b59ae")},
        ),
    ),
)
def test_check_annotators(
    validation_type: ValidationSchema, annotators: Set[UUID]
):
    with pytest.raises(FieldConstraintError):
        check_annotators(annotators, validation_type)
