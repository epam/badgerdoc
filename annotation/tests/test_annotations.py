import json
import uuid
from datetime import datetime
from hashlib import sha1
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy import INTEGER, VARCHAR, Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError

from annotation.annotations.main import (
    MANIFEST,
    S3_START_PATH,
    DuplicateAnnotationError,
    NotConfiguredException,
    connect_s3,
    construct_annotated_doc,
    convert_bucket_name_if_s3prefix,
    create_manifest_json,
    get_sha_of_bytes,
    row_to_dict,
)
from annotation.database import Base
from annotation.models import AnnotatedDoc, Category, File, Job, User
from annotation.schemas.annotations import DocForSaveSchema
from annotation.schemas.categories import CategoryTypeSchema
from annotation.schemas.jobs import JobTypeEnumSchema, ValidationSchema
from tests.override_app_dependency import TEST_TENANT


class AnnotationRow:
    def __init__(
        self,
        uuid_attr: uuid.UUID,
        datetime_attr: datetime,
        str_attr: str,
        int_attr: int,
    ):
        self.uuid_attr = uuid_attr
        self.datetime_attr = datetime_attr
        self.str_attr = str_attr
        self.int_attr = int_attr


class AnnotationRowTable(Base):
    __tablename__ = "test"

    uuid_attr = Column(UUID(as_uuid=True), primary_key=True)
    datetime_attr = Column(DateTime())
    str_attr = Column(VARCHAR)
    int_attr = Column(INTEGER)


SPECIFIC_DATE_TIME = datetime(2024, 1, 1, 10, 10, 0)

CATEGORIES = [
    Category(
        id="18d3d189e73a4680bfa77ba3fe6ebee5",
        name="Test",
        type=CategoryTypeSchema.box,
    ),
]

ANNOTATION_ROW = AnnotationRow(
    uuid_attr=uuid.UUID("34c665fd-ddfb-412c-a3f8-3351d87c6030"),
    datetime_attr=SPECIFIC_DATE_TIME,
    str_attr="test string",
    int_attr=1,
)


ANNOTATION_ROW_TABLE = AnnotationRowTable(
    uuid_attr="34c665fd-ddfb-412c-a3f8-3351d87c6030",
    datetime_attr=SPECIFIC_DATE_TIME,
    str_attr="test string",
    int_attr=1,
)


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

ANNOTATION_EXPECTED_MANIFEST = {
    "pages": {},
    "validated": [1],
    "failed_validation_pages": [],
    "file": "path/to/file",
    "bucket": "bucket-of-phys-file",
    "categories": [
        {"type": "taxonomy", "value": "foo"},
        {"type": "taxonomy", "value": "bar"},
    ],
}

DOC_FOR_SAVE = {
    "base_revision": "20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
    "user": "6ffab2dd-3605-46d4-98a1-2d20011e132d",
    "pages": [
        {
            "page_num": 1,
            "size": {"width": 0.0, "height": 0.0},
            "objs": [
                {
                    "id": 0,
                    "type": "string",
                    "segmentation": {"segment": "string"},
                    "bbox": [0.0, 0.0, 0.0, 0.0],
                    "tokens": None,
                    "links": [{"category_id": 0, "to": 0, "page_num": 1}],
                    "category": "0",
                    "data": {},
                }
            ],
        }
    ],
    "validated": [],
    "failed_validation_pages": [],
    "task_id": 1,
    "links_json": [],
}


@pytest.fixture
def mock_db_query_filter_order_by_all_empty():
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = []

    mock_session = MagicMock()
    mock_session.query.return_value = mock_query
    return mock_session


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "row",
        "expected_dictionary",
    ],
    [
        (
            ANNOTATION_ROW_TABLE,
            {
                "uuid_attr": "34c665fd-ddfb-412c-a3f8-3351d87c6030",
                "datetime_attr": "2024-01-01T10:10:00",
                "str_attr": "test string",
                "int_attr": 1,
            },
            # row_to_dict won't cast INTEGER to string
        ),
        (
            ANNOTATION_ROW,
            {
                "uuid_attr": "34c665fd-ddfb-412c-a3f8-3351d87c6030",
                "datetime_attr": "2024-01-01T10:10:00",
                "str_attr": "test string",
                "int_attr": 1,
            },
            # it return the same as the previous case
        ),
    ],
)
def test_row_to_dict(row, expected_dictionary):
    result = row_to_dict(row)
    print(result)
    assert result == expected_dictionary


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "s3_prefix",
        "bucket_name",
        "expected_string",
    ],
    [
        (
            "S3_test",
            "bucket_test",
            "S3_test-bucket_test",
        ),
        (
            None,
            "bucket_test",
            "bucket_test",
        ),
    ],
)
def test_convert_bucket_name_if_s3prefix(
    monkeypatch,
    s3_prefix,
    bucket_name,
    expected_string,
):
    monkeypatch.setattr("annotation.annotations.main.S3_PREFIX", s3_prefix)
    result = convert_bucket_name_if_s3prefix(bucket_name=bucket_name)
    assert result == expected_string


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "s3_provider",
        "bucket_name",
    ],
    [
        (
            "minio",
            TEST_TENANT,
        ),  # successful connection
        (
            "aws_iam",
            TEST_TENANT,
        ),  # successful connection
        (
            "no_provider",
            TEST_TENANT,
        ),  # NotConfiguredException
        (
            "aws_iam",
            "no_bucket",
        ),  # NoSuchBucket
    ],
)
def test_connect_s3(moto_s3, monkeypatch, s3_provider, bucket_name):
    mock_resource = MagicMock(return_value=moto_s3)
    monkeypatch.setattr("boto3.resource", mock_resource)

    monkeypatch.setattr("annotation.annotations.main.S3_PROVIDER", s3_provider)

    if s3_provider == "no_provider":
        with pytest.raises(NotConfiguredException):
            connect_s3(bucket_name)
    elif bucket_name == "no_bucket":
        with pytest.raises(moto_s3.meta.client.exceptions.NoSuchBucket):
            connect_s3(bucket_name)
    else:
        result_s3 = connect_s3(bucket_name)
        assert moto_s3 == result_s3


@pytest.mark.unittest
def test_get_sha_of_bytes():
    assert sha1(b"1").hexdigest() == get_sha_of_bytes(b"1")


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "annotated_doc",
        "s3_path",
        "phys_path",
        "bucket_physical",
        "expected_manifest",
    ],
    [
        (
            ANNOTATION_DOC_CATEGORIES,
            f"annotation/{str(ANNOTATION_DOC_CATEGORIES.job_id)}/"
            f"{str(ANNOTATION_DOC_CATEGORIES.file_id)}",
            "path/to/file",
            "bucket-of-phys-file",
            ANNOTATION_EXPECTED_MANIFEST,
        )
    ],
)
def test_create_manifest_json(
    moto_s3,
    mock_db_query_filter_order_by_all_empty,
    annotated_doc,
    s3_path,
    phys_path,
    bucket_physical,
    expected_manifest,
):

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
            phys_path,
            bucket_physical,
            ANNOTATION_DOC_CATEGORIES.tenant,
            ANNOTATION_DOC_CATEGORIES.job_id,
            ANNOTATION_DOC_CATEGORIES.file_id,
            mock_db_query_filter_order_by_all_empty,
            moto_s3,
        )
        mock_accumulate_pages_info.assert_called_once_with(
            [], [ANNOTATION_DOC_CATEGORIES], with_page_hash=True
        )
        mock_row_to_dict.assert_called_once_with(ANNOTATION_DOC_CATEGORIES)
        mock_upload_json_to_minio.assert_called_once_with(
            json.dumps(expected_manifest),
            f"{s3_path}/{MANIFEST}",
            ANNOTATION_DOC_CATEGORIES.tenant,
            moto_s3,
        )


@pytest.mark.unittest
@pytest.mark.parametrize(
    [
        "is_latest",
        "new_equal_latest",
        "db_error",
    ],
    [
        (
            True,
            False,
            False,
        ),  # Success path
        (
            True,
            True,
            False,
        ),  # return latest_doc
        (
            False,
            False,
            True,
        ),  # db_error
    ],
)
def test_construct_annotated_doc(
    moto_s3,
    is_latest,
    new_equal_latest,
    db_error,
):
    doc = DocForSaveSchema(**DOC_FOR_SAVE)
    latest_doc = ANNOTATION_DOC_CATEGORIES
    s3_path = f"{S3_START_PATH}/{str(1)}/{str(1)}"

    db = Mock()

    with patch.object(db, "add") as mock_db_add, patch.object(
        db, "add_all"
    ) as mock_db_add_all, patch.object(
        db,
        "commit",
        side_effect=IntegrityError(
            statement="TEST", params=("testuser",), orig=Exception("TESTING")
        )
        if db_error
        else None,
    ) as mock_db_commit, patch.object(
        db, "rollback"
    ) as mock_db_rollback, patch(
        "annotation.annotations.main.get_pages_sha",
        return_value=({"1": "a"}, "b") if is_latest else ({"1": "a"}, "c"),
    ) as mock_get_pages_sha, patch(
        "annotation.annotations.main.check_docs_identity",
        return_value=new_equal_latest,
    ) as mock_check_docs, patch(
        "annotation.annotations.main.construct_document_links", return_value=[]
    ) as mock_construct_doc_links, patch(
        "annotation.annotations.main.convert_bucket_name_if_s3prefix",
        return_value="bucket",
    ) as mock_convert_bucket, patch(
        "annotation.annotations.main.connect_s3", return_value=moto_s3
    ) as mock_connect_s3, patch(
        "annotation.annotations.main.upload_pages_to_minio"
    ) as mock_upload_pages, patch(
        "annotation.annotations.main.create_manifest_json"
    ) as mock_create_manifest:
        if db_error:
            with pytest.raises(DuplicateAnnotationError):
                construct_annotated_doc(
                    db,
                    ANNOTATION_ANNOTATOR.user_id,
                    None,
                    ANNOTATION_DOC_CATEGORIES.job_id,
                    ANNOTATION_DOC_CATEGORIES.file_id,
                    doc,
                    TEST_TENANT,
                    "path",
                    "bucket",
                    latest_doc,
                    1,  # task_id
                    is_latest,
                )
        else:
            construct_annotated_doc(
                db,
                ANNOTATION_ANNOTATOR.user_id,
                None,
                ANNOTATION_DOC_CATEGORIES.job_id,
                ANNOTATION_DOC_CATEGORIES.file_id,
                doc,
                TEST_TENANT,
                "path",
                "bucket",
                latest_doc,
                1,  # task_id
                is_latest,
            )
        if is_latest:
            mock_get_pages_sha.assert_called_once_with(
                doc.pages,
                doc.base_revision,
                doc.validated,
                doc.failed_validation_pages,
                doc.user,
            )
        else:
            mock_get_pages_sha.assert_called_once_with(
                doc.pages,
                latest_doc.revision,
                doc.validated,
                doc.failed_validation_pages,
                doc.user,
            )
        mock_check_docs.assert_called_once()
        if not new_equal_latest:
            mock_construct_doc_links.assert_called_once()
            mock_db_add.assert_called_once()
            mock_db_add_all.assert_called_once_with([])

            if db_error:
                mock_db_commit.assert_called_once()
                mock_db_rollback.assert_called_once()
            else:
                mock_db_commit.assert_called_once()
                mock_convert_bucket.assert_called_once_with(TEST_TENANT)
                mock_connect_s3.assert_called_once_with("bucket")
                mock_upload_pages.assert_called_once_with(
                    pages=doc.pages,
                    pages_sha={"1": "a"},
                    s3_path=s3_path,
                    bucket_name="bucket",
                    s3_resource=moto_s3,
                )
                mock_create_manifest.assert_called_once()
