import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest

from annotation.annotations.main import row_to_dict
from annotation.models import AnnotatedDoc, Category, File, Job, User
from annotation.schemas.categories import CategoryTypeSchema
from annotation.schemas.jobs import JobTypeEnumSchema, ValidationSchema
from tests.override_app_dependency import TEST_TENANT


@pytest.fixture
def categories():
    yield [
        Category(
            id="18d3d189e73a4680bfa77ba3fe6ebee5",
            name="Test",
            type=CategoryTypeSchema.box,
        ),
    ]


@pytest.fixture
def annotation_file():
    yield File(
        **{
            "file_id": 1,
            "tenant": TEST_TENANT,
            "job_id": 1,
            "pages_number": 10,
        }
    )


@pytest.fixture
def annotator():
    yield User(user_id="6ffab2dd-3605-46d4-98a1-2d20011e132d")


@pytest.fixture
def annotation_job(annotator, annotation_file, categories):
    yield Job(
        **{
            "job_id": 1,
            "callback_url": "http://www.test.com/test1",
            "annotators": [annotator],
            "validation_type": ValidationSchema.cross,
            "files": [annotation_file],
            "is_auto_distribution": False,
            "categories": categories,
            "deadline": None,
            "tenant": TEST_TENANT,
            "job_type": JobTypeEnumSchema.ExtractionWithAnnotationJob,
        }
    )


@pytest.fixture
def annotated_doc(
    annotator: User,
    annotation_file: File,
    annotation_job: Job,
):
    yield AnnotatedDoc(
        revision="20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
        user=annotator.user_id,
        pipeline=None,
        date=datetime(2024, 1, 1, 10, 10, 0),
        file_id=annotation_file.file_id,
        job_id=annotation_job.job_id,
        pages={},
        validated=[1],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        categories=["foo", "bar"],
        links_json=[],
    )


def test_row_to_dict_table(annotated_doc: AnnotatedDoc):
    result = row_to_dict(annotated_doc)
    expected_result = {
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
    }
    assert result == expected_result


def test_row_to_dict_non_table():
    mock_dict = Mock()
    mock_dict.__dict__ = {
        "uuid_attr": uuid.UUID("34c665fd-ddfb-412c-a3f8-3351d87c6030"),
        "datetime_attr": datetime(2024, 1, 1, 10, 10, 0),
        "str_attr": "test string",
        "int_attr": 1,
    }
    expected_result = {
        "uuid_attr": "34c665fd-ddfb-412c-a3f8-3351d87c6030",
        "datetime_attr": "2024-01-01T10:10:00",
        "str_attr": "test string",
        "int_attr": 1,
    }
    result = row_to_dict(mock_dict)
    assert result == expected_result
