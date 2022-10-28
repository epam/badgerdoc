from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.db.models import Base
import uuid

import pytest

pytest_plugins = ["docker_compose"]

TEST_DIR = Path(__file__).parent
INTEGRATION_DIR = TEST_DIR / "integration"


@pytest.fixture(scope="module")
def docker_compose_file(pytestconfig):
    return INTEGRATION_DIR / "test-docker-compose.yml"


@pytest.fixture(scope="module")
def jw_token():
    with open(TEST_DIR / "files" / "mock_token.txt") as file:
        jw_token = file.readline()
    return jw_token


@pytest.fixture
def files_data():
    return [
        {
            "id": 1,
            "original_name": "demo.pdf",
            "bucket": "preprocessing",
            "size_in_bytes": 295352,
            "extension": ".pdf",
            "original_ext": None,
            "content_type": "application/pdf",
            "pages": [1, 2, 3],
            "last_modified": "2021-11-02T09:08:15.071851",
            "status": "uploaded",
            "path": "files/1/1.pdf",
            "datasets": [],
        },
        {
            "id": 52,
            "original_name": "sample.pdf",
            "bucket": "mock-for-upload-needs",
            "size_in_bytes": 3028,
            "extension": ".pdf",
            "original_ext": None,
            "content_type": "application/pdf",
            "pages": [1],
            "last_modified": "2021-12-14T08:57:14.188530",
            "status": "uploaded",
            "path": "files/52/52.pdf",
            "datasets": [],
        },
    ]


@pytest.fixture
def files_data_for_pipeline(files_data):
    files_data[0]["pages"] = [1, 2, 3]
    files_data[0]["output_path"] = "path/to/ocr"
    files_data[1]["pages"] = [1]
    files_data[1]["output_path"] = "path/to/ocr"
    return files_data


@pytest.fixture
def setup_database():
    test_db_name = uuid.uuid4().hex
    db_url = f"sqlite:///./{test_db_name}.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    session = session_local()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    remove_db(test_db_name)


def remove_db(db_name):
    base = Path(__file__).parent.parent.parent
    dbs = base.glob(f"**/{db_name}.db")
    for db in dbs:
        db.unlink()
