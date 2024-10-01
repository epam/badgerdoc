import uuid
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from assets.db.models import FileObject
from assets.db.service import (
    delete_file_from_db,
    insert_file,
    update_file_status,
)
from assets.schemas import FileProcessingStatus
from assets.utils.minio_utils import check_bucket, delete_one_from_storage


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


@pytest.mark.skip(reason="tests refactoring")
def test_delete_one_from_db(file_):
    session = file_
    delete_file_from_db(session, 1)
    assert not session.query(FileObject).first()


@pytest.mark.skip(reason="tests refactoring")
def test_check_bucket_negative(minio_mock_exists_bucket_false):
    random_name = uuid.uuid4().hex
    with pytest.raises(HTTPException):
        check_bucket(random_name, minio_mock_exists_bucket_false)
    with pytest.raises(HTTPException):
        check_bucket("1", minio_mock_exists_bucket_false)


@pytest.mark.skip(reason="tests refactoring")
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


def test_delete_one_from_storage(minio_mock_exists_bucket_true):
    with patch("tests.test_helpers.delete_one_from_storage") as mock_:
        mock_.side_effect = [True, False]
        random_name = uuid.uuid4().hex
        minio_mock_exists_bucket_true.fput_object(
            random_name, "testfile", Mock()
        )
        x = delete_one_from_storage(
            random_name, "testfile", minio_mock_exists_bucket_true
        )
        assert x
        y = delete_one_from_storage(
            random_name, "testfile", minio_mock_exists_bucket_true
        )
        assert not y
        minio_mock_exists_bucket_true.remove_bucket(random_name)


@pytest.mark.skip(reason="tests refactoring")
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


@pytest.mark.skip(reason="tests refactoring")
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
