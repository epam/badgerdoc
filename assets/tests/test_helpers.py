import uuid
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from src.db.models import FileObject
from src.db.service import delete_file_from_db, insert_file, update_file_status
from src.schemas import FileProcessingStatus
from src.utils.minio_utils import check_bucket, delete_one_from_minio


@pytest.fixture
def file_(setup_database):
    session = setup_database
    name = "testname"
    file = FileObject(
        original_name=name,
        bucket="testbucket",
        size_in_bytes=1000,
        content_type="application/json",
        extension=".pdf",
        original_ext=".ts",
        status="testing",
    )
    session.add(file)
    session.commit()
    yield session


def test_delete_one_from_db(file_):
    session = file_
    delete_file_from_db(session, 1)
    assert not session.query(FileObject).first()


def test_check_bucket_negative(minio_mock_exists_bucket_false):
    random_name = uuid.uuid4().hex
    with pytest.raises(HTTPException):
        check_bucket(random_name, minio_mock_exists_bucket_false)
    with pytest.raises(HTTPException):
        check_bucket("1", minio_mock_exists_bucket_false)


def test_check_bucket_positive(minio_mock_exists_bucket_true):
    minio_mock_exists_bucket_true.bucket_exists.side_effect = [
        True,
        HTTPException(status_code=404),
    ]
    random_name = uuid.uuid4().hex
    minio_mock_exists_bucket_true.make_bucket(random_name)

    assert check_bucket(random_name, minio_mock_exists_bucket_true)

    with pytest.raises(HTTPException):
        check_bucket(random_name, minio_mock_exists_bucket_true)


def test_delete_one_from_minio(minio_mock_exists_bucket_true):
    with patch("tests.test_helpers.delete_one_from_minio") as mock_:
        mock_.side_effect = [True, False]
        random_name = uuid.uuid4().hex
        minio_mock_exists_bucket_true.fput_object(
            random_name, "testfile", Mock()
        )
        x = delete_one_from_minio(
            random_name, "testfile", minio_mock_exists_bucket_true
        )
        assert x
        y = delete_one_from_minio(
            random_name, "testfile", minio_mock_exists_bucket_true
        )
        assert not y
        minio_mock_exists_bucket_true.remove_bucket(random_name)


def test_put_to_db(setup_database):
    session = setup_database
    f = insert_file(
        session,
        "testfile",
        "some_bucket",
        101,
        ".pdf",
        ".py",
        "app/test",
        1,
        "testing",
    )
    assert f
    assert delete_file_from_db(setup_database, f.id)


def test_update_file_status(file_):
    session = file_
    f = (
        session.query(FileObject)
        .filter(FileObject.original_name == "testname")
        .first()
    )
    assert f
    fi = update_file_status(f.id, FileProcessingStatus.UPLOADED, file_)
    assert fi.status == "uploaded"


def get_test_db_url(main_db_url: str) -> str:
    main_db_url_split = main_db_url.split("/")
    main_db_url_split[-1] = 'test_db'
    result = "/".join(main_db_url_split)
    return result
