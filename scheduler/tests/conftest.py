import os
import time
from unittest import mock
from unittest.mock import patch

import pytest
import sqlalchemy_utils
import tenant_dependency
from fastapi import testclient
from scheduler import app
from scheduler import config as scheduler_config
from scheduler.db import models
from scheduler.db.service import get_test_db_url
from sqlalchemy import create_engine, orm
from sqlalchemy.exc import SQLAlchemyError

from alembic import command
from alembic.config import Config

alembic_cfg = Config("alembic.ini")


@pytest.fixture(scope="session")
def use_temp_env_var():
    with patch.dict(os.environ, {"USE_TEST_DB": "1"}):
        yield


@pytest.fixture
def testing_engine():
    db_url = get_test_db_url(scheduler_config.DB_URL)
    test_db_engine = create_engine(db_url)

    yield test_db_engine
    for _ in range(20):
        try:
            sqlalchemy_utils.drop_database(db_url)
            break
        except PermissionError:
            time.sleep(0.001)


@pytest.fixture
def testing_session(use_temp_env_var, testing_engine):
    sqlalchemy_utils.create_database(testing_engine.url)

    try:
        command.upgrade(alembic_cfg, "head")
    except SQLAlchemyError as e:
        raise SQLAlchemyError("Exception during migrations") from e

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
