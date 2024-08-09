import uuid
from unittest.mock import MagicMock, patch

import pytest

from annotation.errors import (
    EnumValidationError,
    FieldConstraintError,
    WrongJobError,
)
from annotation.jobs.services import check_annotators, update_inner_job_status
from annotation.models import Category, File, Job, User
from annotation.schemas import (
    CategoryTypeSchema,
    FileStatusEnumSchema,
    JobStatusEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)

JOB_TENANT = "test"
ANNOTATORS = (
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
            ANNOTATORS[0],
            ANNOTATORS[1],
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
            ANNOTATORS[0],
            ANNOTATORS[1],
        ],
        validation_type=ValidationSchema.cross,
        is_auto_distribution=False,
        categories=CATEGORIES,
        deadline="2021-10-19T01:01:01",
        tenant=JOB_TENANT,
    ),
)
# FILE_TEST_PROGRESS = File(
#     file_id=1,
#     tenant=JOB_TENANT,
#     job_id=JOB_IDS[0],
#     pages_number=5,
#     status=FileStatusEnumSchema.pending,
# )
# FILE_TEST_PROGRESS_2 = File(
#     file_id=2,
#     tenant=JOB_TENANT,
#     job_id=JOB_IDS[1],
#     pages_number=5,
#     status=FileStatusEnumSchema.pending,
# )
# FILE_TEST_PROGRESS_3 = File(
#     file_id=3,
#     tenant=JOB_TENANT,
#     job_id=JOB_IDS[2],
#     pages_number=5,
#     status=FileStatusEnumSchema.pending,
# )


def test_update_job_status():

    mock_session = MagicMock()

    update_inner_job_status(
        mock_session, JOB_IDS[0], JobStatusEnumSchema.finished
    )

    mock_session.query(Job).filter(
        Job.job_id == JOB_IDS[0]
    ).update.assert_called_with({"status": JobStatusEnumSchema.finished})


@pytest.mark.parametrize(
    "validation_type," "annotators",
    [
        (ValidationSchema.cross, set([uuid.UUID(ANNOTATORS[0].user_id)])),
        (ValidationSchema.hierarchical, set()),
        (
            ValidationSchema.validation_only,
            set([uuid.UUID(ANNOTATORS[0].user_id)]),
        ),
    ],
)
@pytest.mark.unittest
def test_check_annotators_cross(validation_type, annotators):
    if validation_type == ValidationSchema.cross:
        with pytest.raises(FieldConstraintError):
            check_annotators(annotators, validation_type)
    elif validation_type == ValidationSchema.hierarchical:
        with pytest.raises(FieldConstraintError):
            check_annotators(annotators, validation_type)
    elif validation_type == ValidationSchema.validation_only:
        with pytest.raises(FieldConstraintError):
            check_annotators(annotators, validation_type)
