import time
import uuid
from unittest import mock

import sqlalchemy
from sqlalchemy import orm

import pytest
import sqlalchemy_utils
import tenant_dependency
from fastapi import testclient
from scheduler import app
from scheduler.db import models


@pytest.fixture
def testing_engine():
    url = "sqlite:///test.db"
    engine = sqlalchemy.create_engine(url)
    # Replace postgres columns such UUID and JSONB for sqlite compatible.
    models.Base.metadata.tables["units"].append_column(
        sqlalchemy.Column("runner_id", sqlalchemy.String(36)),
        replace_existing=True,
    )
    models.Base.metadata.tables["heartbeat"].append_column(
        sqlalchemy.Column(
            "id",
            sqlalchemy.String(36),
            primary_key=True,
            default=lambda: str(uuid.uuid4()),
        ),
        replace_existing=True,
    )
    yield engine
    for _ in range(20):
        try:
            sqlalchemy_utils.drop_database(url)
            break
        except PermissionError:
            time.sleep(0.001)


@pytest.fixture
def testing_session(testing_engine):
    sqlalchemy_utils.create_database(testing_engine.url)
    models.Base.metadata.create_all(bind=testing_engine)
    Session = orm.sessionmaker(bind=testing_engine, expire_on_commit=False)
    with Session.begin() as session_:
        yield session_


@pytest.fixture
def testing_sessionmaker(testing_engine):
    return orm.sessionmaker(bind=testing_engine, expire_on_commit=False)


@pytest.fixture
def testing_unit_instance():
    yield models.Unit(
        id="uid_1",
        url="url_1",
        body={"arg": "arg"},
        tenant="test_tenant",
        result={"result": "result"},
        status="Finished",
    )


@pytest.fixture
def testing_unit_instance_with_special_tenant():
    yield models.Unit(
        id="uid_2",
        url="url_2",
        body={"arg": "arg"},
        tenant="special_tenant",
        result={"result": "result"},
        status="Finished",
    )


@pytest.fixture
def testing_app(
    testing_session,
    testing_sessionmaker,
    testing_unit_instance,
    testing_unit_instance_with_special_tenant,
):
    def setup_tenant():
        return tenant_dependency.TenantData(
            token="test_token",
            user_id="user_id",
            roles=["role"],
            tenants=["test_tenant"],
        )

    app.app.dependency_overrides[app.tenant] = setup_tenant

    testing_session.add(testing_unit_instance)
    testing_session.add(testing_unit_instance_with_special_tenant)
    testing_session.flush()
    testing_session.commit()

    with mock.patch("scheduler.db.service.Session", testing_sessionmaker):
        client = testclient.TestClient(app.app)
        yield client
