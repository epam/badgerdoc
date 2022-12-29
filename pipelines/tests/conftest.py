import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

import src.app as app
import src.db.models as dbm
import src.db.service as service
import src.execution as execution
import tests.testing_data as td
from alembic import command
from alembic.config import Config
from src.config import DB_URI

test_db_url = service.get_test_db_url(DB_URI)
alembic_cfg = Config("alembic.ini")


@pytest.fixture()
def use_temp_env_var():
    with patch.dict(os.environ, {"USE_TEST_DB": "1"}):
        yield


@pytest.fixture
def testing_engine():
    engine = create_engine(test_db_url)
    yield engine


@pytest.fixture
def setup_test_db(testing_engine):
    if not database_exists(testing_engine.url):
        create_database(testing_engine.url)

    try:
        command.upgrade(alembic_cfg, "head")
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Got an Exception during migrations - {e}")

    yield

    drop_database(test_db_url)


@pytest.fixture
def testing_session(use_temp_env_var, testing_engine, setup_test_db):
    LocalSession = sessionmaker(bind=testing_engine)
    session = LocalSession()
    try:
        yield session
    finally:
        session.close()


class TestTenantData(BaseModel):
    token: str


@pytest.fixture()
def setup_token():
    return TestTenantData(token="some_token")


@pytest.fixture
def testing_app(testing_engine, testing_session, setup_token):
    session = sessionmaker(bind=testing_engine)
    app.app.dependency_overrides[app.TOKEN] = lambda: setup_token
    with patch("src.db.service.LocalSession", session):
        app.app.dependency_overrides[
            service.get_session
        ] = lambda: testing_session
        client = TestClient(app.app)
        yield client


@pytest.fixture
def testing_pipeline():
    yield dbm.Pipeline(
        name="foo",
        version=1,
        type="inference",
        description="some pipeline to execute",
        summary="some pipeline",
        meta=td.meta_dict,
        steps=[td.steps_dict],
    )


@pytest.fixture
def testing_task(testing_pipeline):
    yield dbm.PipelineExecutionTask(
        name="foo", pipeline=testing_pipeline, status="pending", job_id=1
    )


@pytest.fixture
def session_mock():
    with patch("src.db.service.LocalSession") as mock:
        yield mock


@pytest.fixture
def request_mock():
    with patch("src.http_utils.requests.request") as mock:
        yield mock


@pytest.fixture
def run_in_session_mock():
    with patch("src.db.service.run_in_session") as mock:
        yield mock


@pytest.fixture
def mock_preprocessing_file_status():
    async def check_preprocessing_status_mock(x, y):
        return True

    with patch(
        "src.execution.PipelineTask.check_preprocessing_status",
        check_preprocessing_status_mock,
    ) as mock:
        yield mock


@pytest.fixture
def adjust_mock():
    with patch.object(
        execution.Pipeline, "check_valid_ids", return_value={"a": True}
    ):
        with patch.object(execution.Pipeline, "adjust_pipeline") as mock:
            yield mock
