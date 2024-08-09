import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest

from annotation.annotations.main import row_to_dict
from annotation.models import AnnotatedDoc, Category, File, Job, User
from annotation.schemas.categories import CategoryTypeSchema
from annotation.schemas.jobs import JobTypeEnumSchema, ValidationSchema
from tests.override_app_dependency import TEST_TENANT

SPECIFIC_DATE_TIME = datetime(2024, 1, 1, 10, 10, 0)

CATEGORIES = [
    Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    ),
]

ANNOTATION_FILE_1 = File(
    **{
        "file_id": 1,
        "tenant": TEST_TENANT,
        "job_id": 1,
        "pages_number": 10,
    }
)

ANNOTATION_ANNOTATOR = User(user_id="6ffab2dd-3605-46d4-98a1-2d20011e132d")

ANNOTATION_JOB_1 = Job(
    **{
        "job_id": 1,
        "callback_url": "http://www.test.com/test1",
        "annotators": [ANNOTATION_ANNOTATOR],
        "validation_type": ValidationSchema.cross,
        "files": [ANNOTATION_FILE_1],
        "is_auto_distribution": False,
        "categories": CATEGORIES,
        "deadline": None,
        "tenant": TEST_TENANT,
        "job_type": JobTypeEnumSchema.ExtractionWithAnnotationJob,
    }
)

ANNOTATION_DOC_CATEGORIES = AnnotatedDoc(
    revision="20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
    user=ANNOTATION_ANNOTATOR.user_id,
    pipeline=None,
    date=SPECIFIC_DATE_TIME,
    file_id=ANNOTATION_FILE_1.file_id,
    job_id=ANNOTATION_JOB_1.job_id,
    pages={},
    validated=[1],
    failed_validation_pages=[],
    tenant=TEST_TENANT,
    categories=["foo", "bar"],
    links_json=[],
)


def create_mock_dict(d: dict) -> Mock:
    mock_dict = Mock()
    mock_dict.__dict__ = d
    return mock_dict


@pytest.mark.unittest
@pytest.mark.parametrize(
    ["row", "expected_result"],
    [
        (
            ANNOTATION_DOC_CATEGORIES,
            {
                "revision": "20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                "file_id": 1,
                "job_id": 1,
                "user": "6ffab2dd-3605-46d4-98a1-2d20011e132d",
                "pipeline": None,
                "date": "2024-01-01T10:10:00",
                "pages": {},
                "failed_validation_pages": [],
                "validated": [1],
                "tenant": "test",
                "task_id": None,
                "categories": ["foo", "bar"],
                "links_json": [],
            },
            # row_to_dict won't cast INTEGER to string
        ),
        (
            create_mock_dict(
                {
                    "uuid_attr": uuid.UUID(
                        "34c665fd-ddfb-412c-a3f8-3351d87c6030"
                    ),
                    "datetime_attr": SPECIFIC_DATE_TIME,
                    "str_attr": "test string",
                    "int_attr": 1,
                }
            ),
            {
                "uuid_attr": "34c665fd-ddfb-412c-a3f8-3351d87c6030",
                "datetime_attr": "2024-01-01T10:10:00",
                "str_attr": "test string",
                "int_attr": 1,
            },
        ),
    ],
)
def test_row_to_dict(row, expected_result):
    result = row_to_dict(row)
    assert result == expected_result
