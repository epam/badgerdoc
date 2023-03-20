import uuid

import pytest
from assets.db.models import Association, Datasets, FileObject


@pytest.fixture
def dataset(setup_database):
    """
    Puts into database two objects for further tests
    """
    session = setup_database
    file_ = FileObject(
        original_name="testfile",
        bucket="testbucket",
        size_in_bytes=1000,
        content_type="application/json",
        extension="pdf",
        original_ext=".ts",
        status="testing",
    )

    dataset_uid = uuid.uuid4().hex
    dataset_ = Datasets(name=dataset_uid)

    file_.datasets.append(dataset_)
    session.add_all([file_, dataset_])
    session.commit()
    yield session
    session.query(FileObject).delete()
    session.query(Datasets).delete()
    session.query(Association).delete()


def test_database_len(dataset):
    """
    Passes if count of created objects are equal to expected
    """
    session = dataset
    assert len(session.query(FileObject).all()) == 1
    assert len(session.query(Datasets).all()) == 1
    assert len(session.query(Association).all()) == 1


def test_autocreate_association(dataset):
    """
    Passes if Association object generates automatically and
    relation Datasets-Association-FileObject behaves as expected
    """
    session = dataset
    file = session.query(FileObject).first()
    ds = session.query(Datasets).first()
    association = session.query(Association).first()
    assert association.file_id == file.id
    assert association.dataset_id == ds.id


def test_relation(dataset):
    """
    Passes if relation FileObject-Datasets behaves as expected
    """
    session = dataset
    file = session.query(FileObject).first()
    ds = session.query(Datasets).first()
    assert ds in file.datasets


def test_model_property(dataset):
    """
    Passes if models properties returns data in expected format
    """
    session = dataset
    file = session.query(FileObject).first()
    ds = session.query(Datasets).first()

    assert file.as_dict == {
        "id": file.id,
        "original_name": file.original_name,
        "bucket": file.bucket,
        "size_in_bytes": file.size_in_bytes,
        "extension": file.extension,
        "original_ext": file.original_ext,
        "content_type": file.content_type,
        "pages": None,
        "last_modified": file.last_modified,
        "status": file.status,
        "path": file.path,
        "datasets": [ds.name],
    }
    assert ds.as_dict == {
        "id": ds.id,
        "name": ds.name,
        "count": ds.count,
        "created": ds.created,
    }


def test_page_count_jpg_null(setup_database):
    session = setup_database
    file_ = FileObject(
        original_name="testfile",
        bucket="testbucket",
        size_in_bytes=1000,
        content_type="image/jpeg",
        extension="jpeg",
        original_ext=".jpeg",
        status="testing",
        pages=None,
    )
    session.add(file_)
    session.commit()

    f = session.query(FileObject).filter(FileObject.id == file_.id).first()
    assert f.pages == 1


def test_page_count_jpg_not_null(setup_database):
    session = setup_database
    file_ = FileObject(
        original_name="testfile",
        bucket="testbucket",
        size_in_bytes=1000,
        content_type="image/jpeg",
        extension="jpeg",
        original_ext=".jpeg",
        status="testing",
        pages=10,
    )
    session.add(file_)
    session.commit()

    f = session.query(FileObject).filter(FileObject.id == file_.id).first()
    assert f.pages == 10


def test_page_count_any_image_null(setup_database):
    session = setup_database
    file_ = FileObject(
        original_name="testfile",
        bucket="testbucket",
        size_in_bytes=1,
        content_type="image/",
        extension="any",
        original_ext=".any",
        status="testing",
        pages=None,
    )
    session.add(file_)
    session.commit()

    f = session.query(FileObject).filter(FileObject.id == file_.id).first()
    assert f.pages == 1


def test_page_count_not_image_null(setup_database):
    session = setup_database
    file_ = FileObject(
        original_name="testfile",
        bucket="testbucket",
        size_in_bytes=1000,
        content_type="application/json",
        extension="json",
        original_ext=".json",
        status="testing",
        pages=None,
    )
    session.add(file_)
    session.commit()

    f = session.query(FileObject).filter(FileObject.id == file_.id).first()
    assert f.pages is None


def test_page_count_not_image_not_null(setup_database):
    session = setup_database
    file_ = FileObject(
        original_name="testfile",
        bucket="testbucket",
        size_in_bytes=1000,
        content_type="application/txt",
        extension="txt",
        original_ext=".txt",
        status="testing",
        pages=10,
    )
    session.add(file_)
    session.commit()

    f = session.query(FileObject).filter(FileObject.id == file_.id).first()
    assert f.pages == 10
