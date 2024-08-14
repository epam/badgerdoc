import json
import uuid
from datetime import datetime
from hashlib import sha1
from typing import Any, Dict, List
from unittest.mock import ANY, Mock, patch

import boto3
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from tests.override_app_dependency import TEST_TENANT

from annotation.annotations.main import (
    MANIFEST,
    S3_START_PATH,
    DuplicateAnnotationError,
    NotConfiguredException,
    PageRevision,
    check_if_kafka_message_is_needed,
    connect_s3,
    construct_annotated_doc,
    convert_bucket_name_if_s3prefix,
    create_manifest_json,
    get_sha_of_bytes,
    mark_all_revisions_validated_pages,
    row_to_dict,
    update_pages_array,
    upload_json_to_minio,
    upload_pages_to_minio,
)
from annotation.models import AnnotatedDoc, Category, File, Job, User
from annotation.schemas.annotations import (
    AnnotatedDocSchema,
    DocForSaveSchema,
    PageSchema,
)
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


@pytest.fixture
def annotation_doc_for_save():
    yield DocForSaveSchema(
        **{
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
                            "links": [
                                {"category_id": 0, "to": 0, "page_num": 1}
                            ],
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
    )


@pytest.fixture
def annotated_doc_schema(annotator):
    yield AnnotatedDocSchema(
        revision="20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
        user=annotator.user_id,
        pipeline=None,
        date=datetime(2024, 1, 1, 10, 10, 0),
        file_id=1,
        job_id=1,
        pages={
            "1": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
            "2": "adda414648714f01c1c9657646b72ebb4433c8b5",
        },
        validated={1, 2, 10},
        failed_validation_pages={3, 4},
        tenant="badger-doc",
        task_id=2,
        similar_revisions=None,
        categories={"1", "2"},
        links_json=[
            {"to": 2, "category": "my_category", "type": "directional"}
        ],
    )


@pytest.fixture
def page_revision_list(annotated_doc_schema):
    yield {
        1: [
            {
                "user_id": annotated_doc_schema.user,
                "pipeline": annotated_doc_schema.pipeline,
                "job_id": annotated_doc_schema.job_id,
                "file_id": annotated_doc_schema.file_id,
                "revision": annotated_doc_schema.revision,
                "page_id": None,
                "date": annotated_doc_schema.date,
                "is_validated": False,
                "categories": annotated_doc_schema.categories,
            }
        ],
        2: [
            {
                "user_id": uuid.UUID("82aa573f-43d8-40ab-8837-282b315f7c3a"),
                "pipeline": annotated_doc_schema.pipeline,
                "job_id": annotated_doc_schema.job_id,
                "file_id": annotated_doc_schema.file_id,
                "revision": annotated_doc_schema.revision,
                "page_id": None,
                "date": annotated_doc_schema.date,
                "is_validated": False,
                "categories": annotated_doc_schema.categories,
            }
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


def test_construct_annotated_doc(
    annotated_doc: AnnotatedDoc,
    annotation_doc_for_save: DocForSaveSchema,
):
    doc = annotation_doc_for_save
    latest_doc = annotated_doc
    s3_path = f"{S3_START_PATH}/{annotated_doc.job_id}/{annotated_doc.file_id}"
    s3_file_path = "path"
    s3_file_bucket = "bucket"

    pages_sha_non_latest = ({"1": "a"}, "c")

    expected_doc = AnnotatedDoc(
        user=annotated_doc.user,
        pipeline=None,
        file_id=annotated_doc.file_id,
        job_id=annotated_doc.job_id,
        validated=doc.validated,
        failed_validation_pages=doc.failed_validation_pages,
        tenant=TEST_TENANT,
        task_id=1,
        links_json=doc.links_json,
        categories=doc.categories or [],
    )

    expected_doc.pages = pages_sha_non_latest[0]
    expected_doc.revision = pages_sha_non_latest[1]

    db = Mock()

    with patch(
        "annotation.annotations.main.get_pages_sha",
        return_value=pages_sha_non_latest,
    ) as mock_get_pages_sha, patch(
        "annotation.annotations.main.check_docs_identity",
        return_value=False,
    ) as mock_check_docs, patch(
        "annotation.annotations.main.construct_document_links", return_value=[]
    ) as mock_construct_doc_links, patch(
        "annotation.annotations.main.convert_bucket_name_if_s3prefix",
        return_value=TEST_TENANT,
    ) as mock_convert_bucket, patch(
        "annotation.annotations.main.upload_pages_to_minio"
    ) as mock_upload_pages, patch(
        "annotation.annotations.main.create_manifest_json"
    ) as mock_create_manifest:
        actual_doc = construct_annotated_doc(
            db,
            annotated_doc.user,
            None,
            annotated_doc.job_id,
            annotated_doc.file_id,
            doc,
            TEST_TENANT,
            s3_file_path,
            s3_file_bucket,
            latest_doc,
            1,
            is_latest=False,
        )

        mock_get_pages_sha.assert_called_once_with(
            doc.pages,
            latest_doc.revision,
            doc.validated,
            doc.failed_validation_pages,
            doc.user,
        )
        mock_check_docs.assert_called_once_with(
            latest_doc=latest_doc, new_doc=expected_doc
        )

        mock_construct_doc_links.assert_called_once_with(
            expected_doc, doc.similar_revisions or []
        )
        db.add.assert_called_once()
        db.add_all.assert_called_once_with([])
        db.commit.assert_called_once()
        mock_convert_bucket.assert_called_once_with(TEST_TENANT)
        mock_upload_pages.assert_called_once_with(
            pages=doc.pages,
            pages_sha=pages_sha_non_latest[0],
            s3_path=s3_path,
            bucket_name=TEST_TENANT,
            s3_resource=None,
        )
        mock_create_manifest.assert_called_once_with(
            expected_doc,
            s3_path,
            s3_file_path,
            s3_file_bucket,
            TEST_TENANT,
            annotated_doc.job_id,
            annotated_doc.file_id,
            db,
            None,
        )
        assert actual_doc == expected_doc


def test_construct_annotated_doc_new_equals_latest(
    annotated_doc: AnnotatedDoc,
    annotation_doc_for_save: DocForSaveSchema,
):
    doc = annotation_doc_for_save
    latest_doc = annotated_doc

    s3_file_path = "path"
    s3_file_bucket = "bucket"

    pages_sha_latest = ({"1": "a"}, "b")
    expected_doc = AnnotatedDoc(
        user=annotated_doc.user,
        pipeline=None,
        file_id=annotated_doc.file_id,
        job_id=annotated_doc.job_id,
        validated=doc.validated,
        failed_validation_pages=doc.failed_validation_pages,
        tenant=TEST_TENANT,
        task_id=1,
        links_json=doc.links_json,
        categories=doc.categories or [],
    )

    expected_doc.pages = pages_sha_latest[0]
    expected_doc.revision = pages_sha_latest[1]
    db = Mock()

    with patch(
        "annotation.annotations.main.get_pages_sha",
        return_value=pages_sha_latest,
    ) as mock_get_pages_sha, patch(
        "annotation.annotations.main.check_docs_identity",
        return_value=True,
    ) as mock_check_docs:
        actual_doc = construct_annotated_doc(
            db,
            annotated_doc.user,
            None,
            annotated_doc.job_id,
            annotated_doc.file_id,
            doc,
            TEST_TENANT,
            s3_file_path,
            s3_file_bucket,
            latest_doc,
            1,
            is_latest=True,
        )

        mock_get_pages_sha.assert_called_once_with(
            doc.pages,
            doc.base_revision,
            doc.validated,
            doc.failed_validation_pages,
            doc.user,
        )
        mock_check_docs.assert_called_once_with(
            latest_doc=latest_doc, new_doc=expected_doc
        )
        assert actual_doc == latest_doc


def test_construct_annotated_doc_db_error(
    annotated_doc: AnnotatedDoc,
    annotation_doc_for_save: DocForSaveSchema,
):
    new_equal_latest = False
    doc = annotation_doc_for_save
    latest_doc = annotated_doc
    s3_file_path = "path"
    s3_file_bucket = "bucket"

    pages_sha_non_latest = ({"1": "a"}, "c")

    db = Mock()
    db.commit.side_effect = IntegrityError(
        statement="TEST", params=("testuser",), orig=Exception("TESTING")
    )

    with patch(
        "annotation.annotations.main.get_pages_sha",
        return_value=pages_sha_non_latest,
    ), patch(
        "annotation.annotations.main.check_docs_identity",
        return_value=new_equal_latest,
    ), patch(
        "annotation.annotations.main.construct_document_links", return_value=[]
    ):
        with pytest.raises(DuplicateAnnotationError):
            construct_annotated_doc(
                db,
                annotated_doc.user,
                None,
                annotated_doc.job_id,
                annotated_doc.file_id,
                doc,
                TEST_TENANT,
                s3_file_path,
                s3_file_bucket,
                latest_doc,
                1,
                is_latest=False,
            )
            assert db.commit.assert_called_once()
            assert db.rollback.assert_called_once()


def test_upload_json_to_minio():
    test_json = json.dumps({"test": 1})
    path_to_object = "path"
    bucket_name = TEST_TENANT

    with patch(
        "annotation.annotations.main.bd_storage.get_storage"
    ) as mock_get_storage:
        mock_get_storage.return_value.upload_obj = Mock()

        upload_json_to_minio(test_json, path_to_object, bucket_name, None)
        mock_get_storage.assert_called_once_with(bucket_name)
        mock_get_storage().upload_obj.assert_called_once_with(
            target_path=path_to_object, file=ANY
        )


def test_upload_pages_to_minio(moto_s3: boto3.resource):
    pages = [PageSchema(page_num=1, size={}, objs=[])]
    pages_sha = {"1": "sha1"}
    s3_path = "path"
    with patch(
        "annotation.annotations.main.upload_json_to_minio"
    ) as mock_upload_json:
        upload_pages_to_minio(pages, pages_sha, s3_path, TEST_TENANT, moto_s3)
        path_to_object = f"{s3_path}/{pages_sha[str(pages[0].page_num)]}.json"
        mock_upload_json.assert_called_once_with(
            json.dumps(pages[0].dict()), path_to_object, TEST_TENANT, moto_s3
        )


def test_update_pages_array():
    resulting_set = update_pages_array({1, 2, 3}, {4}, {1, 2})
    assert resulting_set == {3, 4}


def test_kafka_message_needed(annotated_doc: AnnotatedDoc):
    db = Mock()
    check_if_kafka_message_is_needed(
        db,
        annotated_doc,
        annotated_doc,
        annotated_doc.job_id,
        annotated_doc.file_id,
        TEST_TENANT,
    )
    db.assert_not_called


def test_kafka_message_needed_commit(annotated_doc: AnnotatedDoc):
    db = Mock()
    db.commit = Mock()
    check_if_kafka_message_is_needed(
        db,
        annotated_doc,
        None,
        annotated_doc.job_id,
        annotated_doc.file_id,
        TEST_TENANT,
    )
    db.commit.assert_called_once()


def test_mark_all_revs_validated_pages(
    page_revision_list: Dict[int, List[PageRevision]],
    annotated_doc_schema: AnnotatedDocSchema,
):
    expected_pages = {
        1: [
            {
                "user_id": annotated_doc_schema.user,
                "pipeline": None,
                "job_id": 1,
                "file_id": 1,
                "revision": "20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                "page_id": None,
                "date": datetime(2024, 1, 1, 10, 10),
                "is_validated": True,
                "categories": {"2", "1"},
            }
        ],
        2: [
            {
                "user_id": uuid.UUID("82aa573f-43d8-40ab-8837-282b315f7c3a"),
                "pipeline": annotated_doc_schema.pipeline,
                "job_id": annotated_doc_schema.job_id,
                "file_id": annotated_doc_schema.file_id,
                "revision": annotated_doc_schema.revision,
                "page_id": None,
                "date": annotated_doc_schema.date,
                "is_validated": False,
                "categories": annotated_doc_schema.categories,
            },
            {
                "user_id": annotated_doc_schema.user,
                "pipeline": None,
                "job_id": 1,
                "file_id": 1,
                "revision": "20fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                "page_id": None,
                "date": datetime(2024, 1, 1, 10, 10),
                "is_validated": True,
                "categories": {"2", "1"},
            },
        ],
    }

    mark_all_revisions_validated_pages(
        page_revision_list, annotated_doc_schema, {1, 2}
    )

    assert page_revision_list == expected_pages
