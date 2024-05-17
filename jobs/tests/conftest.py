import os
import time
from typing import List, Literal
from unittest.mock import patch

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker  # type: ignore
from sqlalchemy_utils import (  # type: ignore
    create_database,
    database_exists,
    drop_database,
)

import jobs.db_service as service
import jobs.main as main
from jobs import pipeline

pytest_plugins = [
    "tests.fixtures_models",
    "tests.fixtures_schemas",
]

pytest_plugins = [
    "tests.fixtures_models",
    "tests.fixtures_schemas",
]

alembic_cfg = Config("alembic.ini")


class FakePipeline(pipeline.BasePipeline):
    calls = []

    async def list(self) -> List[pipeline.AnyPipeline]:
        return []

    async def run(self, **kwargs) -> None:
        FakePipeline.calls.append(kwargs)
        return None


@pytest.fixture(scope="session")
def use_temp_env_var():
    with patch.dict(os.environ, {"USE_TEST_DB": "1"}):
        yield


@pytest.fixture
def test_db_url():
    yield "postgresql+psycopg2://admin:admin@localhost:5432/test_db"


@pytest.fixture
def testing_engine(test_db_url):
    engine = create_engine(test_db_url)

    yield engine


@pytest.fixture
def setup_test_db(testing_engine, use_temp_env_var, test_db_url):
    if not database_exists(testing_engine.url):
        create_database(testing_engine.url)

    try:
        command.upgrade(alembic_cfg, "head")

    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Got an Exception during migrations - {e}")

    yield

    for _ in range(20):
        try:
            drop_database(test_db_url)
            break
        except PermissionError:
            time.sleep(0.001)


@pytest.fixture
def testing_session(testing_engine, setup_test_db):
    SessionLocal = sessionmaker(bind=testing_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def jw_token():
    with open("./tests/mock_token.txt") as file:
        jw_token = file.readline()
    return jw_token


class TenantData(BaseModel):
    token: str
    user_id: str
    roles: List[str]
    tenants: List[str]


@pytest.fixture()
def setup_tenant():
    mock_tenant_data = TenantData(
        token="token",
        user_id="owner1",
        roles=["admin"],
        tenants=["tenant", "test"],
    )
    return mock_tenant_data


async def patched_create_pre_signed_s3_url(
    bucket: str,
    path: str,
    action: Literal["get_object"] = "get_object",
    expire_in_hours: int = 48,
):
    return (
        f"http://example.storage/"
        f"{bucket.strip('./')}/{path.strip('./')}?some-fake-arg=1"
    )


@pytest.fixture
def testing_app(testing_engine, testing_session, setup_tenant):
    with (
        patch("jobs.db_service.LocalSession", testing_session),
        patch(
            "jobs.s3.create_pre_signed_s3_url",
            patched_create_pre_signed_s3_url,
        ),
    ):
        main.app.dependency_overrides[main.tenant] = lambda: setup_tenant
        main.app.dependency_overrides[service.get_session] = (
            lambda: testing_session
        )
        client = TestClient(main.app)
        yield client


@pytest.fixture
def mock_data_dataset11():
    mock_data_dataset11 = [
        {
            "id": 1,
            "original_name": "3.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 44900,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 10,
            "last_modified": "2021-10-22T07:00:31.964897",
            "status": "uploaded",
            "path": "files/1/1.pdf",
            "datasets": ["dataset11"],
        },
        {
            "id": 2,
            "original_name": "4.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 30111,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 2,
            "last_modified": "2021-10-22T07:00:32.106530",
            "status": "uploaded",
            "path": "files/2/2.pdf",
            "datasets": ["dataset11"],
        },
    ]
    return mock_data_dataset11


@pytest.fixture
def mock_data_dataset22():
    mock_data_dataset22 = [
        {
            "id": 3,
            "original_name": "33.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 917433,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 6,
            "last_modified": "2021-10-22T07:00:32.239522",
            "status": "uploaded",
            "path": "files/3/3.pdf",
            "datasets": ["dataset22"],
        },
        {
            "id": 4,
            "original_name": "44.pdf",
            "bucket": "bucket11",
            "size_in_bytes": 2680002,
            "extension": ".pdf",
            "content_type": "application/pdf",
            "pages": 32,
            "last_modified": "2021-10-22T07:00:32.398579",
            "status": "uploaded",
            "path": "files/4/4.pdf",
            "datasets": ["dataset22"],
        },
    ]
    return mock_data_dataset22


@pytest.fixture
def request_body_for_invalid_file():
    request_body = {
        "pagination": {"page_num": 1, "page_size": 15},
        "filters": [
            {"field": "id", "operator": "eq", "value": "some invalid file id"}
        ],
        "sorting": [{"field": "id", "direction": "asc"}],
    }
    return request_body


@pytest.fixture
def pipeline_info_from_pipeline_manager():
    pipeline_info_from_pipeline_manager = {
        "id": 2,
        "name": "pipeline",
        "version": "v1",
        "date": "2021-12-22T09:59:28.142508",
        "meta": {
            "categories": [
                "title",
                "header",
                "table",
                "figure",
                "footer",
                "not_chart",
                "text",
                "chart",
                "molecule",
            ]
        },
        "steps": [
            {
                "id": "58143e43-9a3b-4ab3-ba0c-c8d0ce4629e1",
                "model": "dod",
                "model_url": "http://dod.dev1/v1/models/dod:predict",
                "categories": ["label"],
                "args": {},
                "steps": [
                    {
                        "id": "7571f17b-d9f1-4d31-af42-7f29fbfd0fb9",
                        "model": "ternary",
                        "model_url": "http://ternary.dev1/v1/models/"
                        "ternary:predict",
                        "categories": ["mrt"],
                        "steps": [],
                    }
                ],
            }
        ],
    }
    return pipeline_info_from_pipeline_manager


@pytest.fixture
def separate_files_1_2_data_from_dataset_manager():
    separate_files_1_2_data_from_dataset_manager = {
        "pagination": {
            "page_num": 1,
            "page_size": 15,
            "min_pages_left": 1,
            "total": 2,
            "has_more": False,
        },
        "data": [
            {
                "id": 1,
                "original_name": "3.pdf",
                "bucket": "tenant1",
                "size_in_bytes": 44900,
                "extension": ".pdf",
                "content_type": "application/pdf",
                "pages": 10,
                "last_modified": "2021-11-19T12:26:18.815466",
                "status": "uploaded",
                "path": "files/1/1.pdf",
                "datasets": ["dataset11"],
            },
            {
                "id": 2,
                "original_name": "4.pdf",
                "bucket": "tenant1",
                "size_in_bytes": 30111,
                "extension": ".pdf",
                "content_type": "application/pdf",
                "pages": 2,
                "last_modified": "2021-11-19T12:26:18.959314",
                "status": "uploaded",
                "path": "files/2/2.pdf",
                "datasets": ["dataset11"],
            },
        ],
    }
    return separate_files_1_2_data_from_dataset_manager


@pytest.fixture
def user1_data():
    user1_data = {
        "access": {
            "manageGroupMembership": False,
            "view": True,
            "mapRoles": False,
            "impersonate": False,
            "manage": False,
        },
        "attributes": {"tenants": ["test"]},
        "clientConsents": None,
        "clientRoles": None,
        "createdTimestamp": 1645544502633,
        "credentials": None,
        "disableableCredentialTypes": [],
        "email": None,
        "emailVerified": False,
        "enabled": True,
        "federatedIdentities": [],
        "federationLink": None,
        "firstName": None,
        "groups": None,
        "id": "45526cca-291a-405e-8234-6088454e18c4",
        "lastName": None,
        "notBefore": 0,
        "origin": None,
        "realmRoles": None,
        "requiredActions": [],
        "self": None,
        "serviceAccountClientId": None,
        "username": "annotator",
    }
    return user1_data


@pytest.fixture
def user2_data():
    user2_data = {
        "access": {
            "manageGroupMembership": False,
            "view": True,
            "mapRoles": False,
            "impersonate": False,
            "manage": False,
        },
        "attributes": None,
        "clientConsents": None,
        "clientRoles": None,
        "createdTimestamp": 1672758840502,
        "credentials": None,
        "disableableCredentialTypes": [],
        "email": "annotator2@maiil.com",
        "emailVerified": True,
        "enabled": True,
        "federatedIdentities": [],
        "federationLink": None,
        "firstName": "annotator2",
        "groups": None,
        "id": "3675d181-9d31-4d59-91fc-9b24e3a8e486",
        "lastName": "annotatorov",
        "notBefore": 0,
        "origin": None,
        "realmRoles": None,
        "requiredActions": [],
        "self": None,
        "serviceAccountClientId": None,
        "username": "annotator2",
    }
    return user2_data
