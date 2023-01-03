import os
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from alembic import command
from alembic.config import Config
from src.config import settings
from src.db.service import get_test_db_url

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


alembic_cfg = Config("alembic.ini")


@pytest.fixture(scope="session")
def use_temp_env_var():
    with patch.dict(os.environ, {"USE_TEST_DB": "1"}):
        yield


@pytest.fixture
def db_test_engine():
    db_url = get_test_db_url(settings.database_url)
    test_db_engine = create_engine(db_url)
    yield test_db_engine


@pytest.fixture
def setup_database(use_temp_env_var, db_test_engine):

    if not database_exists(db_test_engine.url):
        create_database(db_test_engine.url)

    try:
        command.upgrade(alembic_cfg, "head")
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Got an Exception during migrations - {e}")

    yield

    drop_database(db_test_engine.url)


@pytest.fixture
def db_test_session(db_test_engine, setup_database):
    session_local = sessionmaker(bind=db_test_engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
