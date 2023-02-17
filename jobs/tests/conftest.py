import datetime
import os
import time
from typing import List
from unittest.mock import patch

import jobs.db_service as service
import jobs.main as main
import jobs.schemas as schemas
import pytest
from fastapi.testclient import TestClient
from jobs.utils import get_test_db_url
from pydantic import BaseModel
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker  # type: ignore
from sqlalchemy_utils import (  # type: ignore
    create_database,
    database_exists,
    drop_database,
)

from alembic import command
from alembic.config import Config

main_database_url = os.environ.get("POSTGRESQL_JOBMANAGER_DATABASE_URI")
test_db_url = get_test_db_url(main_database_url)
alembic_cfg = Config("alembic.ini")


@pytest.fixture(scope="session")
def use_temp_env_var():
    with patch.dict(os.environ, {"USE_TEST_DB": "1"}):
        yield


@pytest.fixture
def testing_engine():
    engine = create_engine(test_db_url)

    yield engine


@pytest.fixture
def setup_test_db(testing_engine, use_temp_env_var):
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


@pytest.fixture
def testing_app(testing_engine, testing_session, setup_tenant):
    with patch("jobs.db_service.LocalSession", testing_session):
        main.app.dependency_overrides[main.tenant] = lambda: setup_tenant
        main.app.dependency_overrides[
            service.get_session
        ] = lambda: testing_session
        client = TestClient(main.app)
        yield client


@pytest.fixture()
def mock_ExtractionJobParams():
    mockExtractionJobParams = schemas.ExtractionJobParams(
        name="MockExtractionJobParams",
        files=[1, 2],
        datasets=[1, 2],
        pipeline_name="MockPipeline",
    )
    return mockExtractionJobParams


@pytest.fixture
def mock_AnnotationJobParams():
    mockAnnotationJobParams = schemas.AnnotationJobParams(
        name="MockAnnotationJob",
        datasets=[1, 2],
        files=[1, 2],
        annotators=["annotator1", "annotator2"],
        validators=["validator1", "validator2"],
        owners=["owner1"],
        categories=["category1", "category2"],
        validation_type="cross",
        is_auto_distribution=False,
        deadline=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )
    return mockAnnotationJobParams


@pytest.fixture
def mock_AnnotationJobParams2():
    mockAnnotationJobParams2 = schemas.AnnotationJobParams(
        name="MockAnnotationJob",
        datasets=[1, 2],
        files=[1, 2],
        annotators=["annotator1", "annotator2"],
        validators=["validator1", "validator2"],
        owners=["owner2"],
        categories=["category1", "category2"],
        validation_type="cross",
        is_auto_distribution=False,
        deadline=datetime.datetime.utcnow() + datetime.timedelta(days=1),
    )
    return mockAnnotationJobParams2


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
