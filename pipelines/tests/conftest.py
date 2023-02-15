import time
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, drop_database
import src.app as app
import src.db.models as dbm
import src.db.service as service
import src.execution as execution
import tests.testing_data as td


@pytest.fixture
def testing_engine():
    url = "sqlite:///test.db"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    # Replace postgres columns such UUID and JSONB for sqlite compatible.
    dbm.Base.metadata.tables["pipeline_execution_task"].append_column(
        Column("runner_id", String(36))
    )
    dbm.Base.metadata.tables["execution_step"].append_column(
        Column("step_id", String(36))
    )
    dbm.Base.metadata.tables["execution_step"].append_column(
        Column("parent_step", String(36))
    )
    dbm.Base.metadata.tables["heartbeat"].append_column(
        Column(
            "id",
            String(36),
            primary_key=True,
            default=lambda: str(uuid.uuid4()),
        )
    )
    dbm.Base.metadata.tables["main_event_log"].append_column(
        Column("runner_id", String(36))
    )
    dbm.Base.metadata.tables["main_event_log"].append_column(
        Column("event", JSON(none_as_null=True))
    )
    yield engine
    for _ in range(20):
        try:
            drop_database(url)
            break
        except PermissionError:
            time.sleep(0.001)


@pytest.fixture
def testing_session(testing_engine):
    create_database(testing_engine.url)
    dbm.Base.metadata.create_all(bind=testing_engine)
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
    create_database(testing_engine.url)
    dbm.Base.metadata.create_all(bind=testing_engine)
    session = sessionmaker(bind=testing_engine)
    app.app.dependency_overrides[app.TOKEN] = lambda: setup_token
    with patch("users.db.service.LocalSession", session):
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
    with patch("users.db.service.LocalSession") as mock:
        yield mock


@pytest.fixture
def request_mock():
    with patch("users.http_utils.requests.request") as mock:
        yield mock


@pytest.fixture
def run_in_session_mock():
    with patch("users.db.service.run_in_session") as mock:
        yield mock


@pytest.fixture
def mock_preprocessing_file_status():
    async def check_preprocessing_status_mock(x, y):
        return True

    with patch(
        "users.execution.PipelineTask.check_preprocessing_status",
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
