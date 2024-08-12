import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest

from annotation.annotations.main import row_to_dict
from annotation.models import AnnotatedDoc, Category, File, Job, User
from annotation.schemas.categories import CategoryTypeSchema
from annotation.schemas.jobs import JobTypeEnumSchema, ValidationSchema
from tests.override_app_dependency import TEST_TENANT


@pytest.fixture(scope="function")
def specific_date_and_time():
    SPECIFIC_DATE_TIME = datetime(2024, 1, 1, 10, 10, 0)
    yield SPECIFIC_DATE_TIME


@pytest.fixture(scope="function")
def categories():
    CATEGORIES = [
        Category(
            id="18d3d189e73a4680bfa77ba3fe6ebee5",
            name="Test",
            type=CategoryTypeSchema.box,
        ),
    ]
    yield CATEGORIES


@pytest.fixture(scope="function")
def annotation_file():
    ANNOTATION_FILE_1 = File(
        **{
            "file_id": 1,
            "tenant": TEST_TENANT,
            "job_id": 1,
            "pages_number": 10,
        }
    )
    yield ANNOTATION_FILE_1


@pytest.fixture(scope="function")
def annotator():
    ANNOTATION_ANNOTATOR = User(user_id="6ffab2dd-3605-46d4-98a1-2d20011e132d")
    yield ANNOTATION_ANNOTATOR


@pytest.fixture(scope="function")
def annotation_job(annotator, annotation_file, categories):
    ANNOTATION_JOB_1 = Job(
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

    yield ANNOTATION_JOB_1


@pytest.fixture(scope="function")
def annotated_doc(
    annotator: User,
    specific_date_and_time: datetime,
    annotation_file: File,
    annotation_job: Job,
):
    ANNOTATION_DOC_CATEGORIES = AnnotatedDoc(
        revision="20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
        user=annotator.user_id,
        pipeline=None,
        date=specific_date_and_time,
        file_id=annotation_file.file_id,
        job_id=annotation_job.job_id,
        pages={},
        validated=[1],
        failed_validation_pages=[],
        tenant=TEST_TENANT,
        categories=["foo", "bar"],
        links_json=[],
    )
    yield ANNOTATION_DOC_CATEGORIES


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


def test_row_to_dict_non_table(specific_date_and_time: datetime):
    mock_dict = Mock()
    mock_dict.__dict__ = {
        "uuid_attr": uuid.UUID("34c665fd-ddfb-412c-a3f8-3351d87c6030"),
        "datetime_attr": specific_date_and_time,
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
