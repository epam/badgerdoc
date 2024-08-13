import json
import uuid
from datetime import datetime
from hashlib import sha1
from typing import Any, Dict
from unittest.mock import Mock, patch

import boto3
import pytest
from sqlalchemy.orm import Session
from tests.override_app_dependency import TEST_TENANT

from annotation.annotations.main import (
    MANIFEST,
    NotConfiguredException,
    connect_s3,
    convert_bucket_name_if_s3prefix,
    create_manifest_json,
    get_sha_of_bytes,
    row_to_dict,
)
from annotation.models import AnnotatedDoc, Category, File, Job, User
from annotation.schemas.categories import CategoryTypeSchema
from annotation.schemas.jobs import JobTypeEnumSchema, ValidationSchema


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
def annotation_job(annotator: User, annotation_file: File, categories: Job):
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


@pytest.fixture
def annotation_manifest():
    yield {
        "pages": {},
        "validated": [1],
        "failed_validation_pages": [],
        "file": "path/to/file",
        "bucket": "file-bucket",
        "categories": [
            {"type": "taxonomy", "value": "foo"},
            {"type": "taxonomy", "value": "bar"},
        ],
    }


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


@pytest.mark.parametrize(
    ("s3_prefix", "bucket_name", "expected_string"),
    (
        ("S3_test", "bucket_test", "S3_test-bucket_test"),
        (None, "bucket_test", "bucket_test"),
    ),
)
def test_convert_bucket_name_if_s3prefix(
    s3_prefix: str,
    bucket_name: str,
    expected_string: str,
):
    with patch("annotation.annotations.main.S3_PREFIX", s3_prefix):
        result = convert_bucket_name_if_s3prefix(bucket_name=bucket_name)
    assert result == expected_string


@pytest.mark.parametrize(
    "s3_provider",
    ("minio", "aws_iam"),
)
def test_connect_s3(moto_s3: boto3.resource, s3_provider: str):
    with patch("boto3.resource", return_value=moto_s3) as mock_resource, patch(
        "annotation.annotations.main.STORAGE_PROVIDER", s3_provider
    ):
        result_s3 = connect_s3(TEST_TENANT)
        mock_resource.assert_called_once()
    assert result_s3 == moto_s3


def test_connect_s3_no_provider(moto_s3: boto3.resource):
    with patch("boto3.resource", return_value=moto_s3), patch(
        "annotation.annotations.main.STORAGE_PROVIDER", "NO_PROVIDER"
    ):
        with pytest.raises(NotConfiguredException):
            connect_s3(TEST_TENANT)


def test_connect_s3_no_bucket(moto_s3: boto3.resource):
    with patch("boto3.resource", return_value=moto_s3), patch(
        "annotation.annotations.main.STORAGE_PROVIDER", "aws_iam"
    ):
        with pytest.raises(moto_s3.meta.client.exceptions.NoSuchBucket):
            connect_s3("NO_BUCKET")


def test_get_sha_of_bytes():
    assert sha1(b"1").hexdigest() == get_sha_of_bytes(b"1")


def test_create_manifest_json(
    moto_s3: boto3.resource,
    annotated_doc: AnnotatedDoc,
    annotation_manifest: Dict[str, Any],
):
    db = Mock(spec=Session)
    db.query().filter().order_by().all.return_value = []
    s3_path = f"annotation/{annotated_doc.job_id}/{annotated_doc.file_id}"
    s3_file_path = "path/to/file"
    s3_file_bucket = "file-bucket"

    with patch(
        "annotation.annotations.main.accumulate_pages_info",
        return_value=[{1: "validated"}, {}, {}],
    ) as mock_accumulate_pages_info, patch(
        "annotation.annotations.main.row_to_dict"
    ) as mock_row_to_dict, patch(
        "annotation.annotations.main.upload_json_to_minio"
    ) as mock_upload_json_to_minio:
        create_manifest_json(
            annotated_doc,
            s3_path,
            s3_file_path,
            s3_file_bucket,
            annotated_doc.tenant,
            annotated_doc.job_id,
            annotated_doc.file_id,
            db,
            moto_s3,
        )
        mock_accumulate_pages_info.assert_called_once_with(
            [], [annotated_doc], with_page_hash=True
        )
        mock_row_to_dict.assert_called_once_with(annotated_doc)
        mock_upload_json_to_minio.assert_called_once_with(
            json.dumps(annotation_manifest),
            f"{s3_path}/{MANIFEST}",
            annotated_doc.tenant,
            moto_s3,
        )
