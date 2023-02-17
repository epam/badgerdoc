from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from usage_example.jwt_generator import create_access_token

from src import TenantData
from src.dependency import get_tenant_info

SECRET_KEY = "test_secret_key"


def get_key(filename: str) -> str:
    path = Path(__file__).parent / filename
    with open(path, encoding="utf-8") as file_out:
        return file_out.read()


private_key = get_key("private_key")
public_key = get_key("public_key")


@pytest.fixture
def mock_jwk_client():
    with patch("src.dependency.jwt.PyJWKClient.__init__", return_value=None) as mock:
        yield mock


@pytest.fixture
def mock_sig_key():
    m = MagicMock()
    m.key = public_key
    with patch(
        "src.dependency.jwt.PyJWKClient.get_signing_key_from_jwt",
        return_value=m,
    ) as mock:
        yield mock


@pytest.fixture
def test_app_rs256(mock_jwk_client, mock_sig_key):
    app = FastAPI()
    tenant = get_tenant_info(algorithm="RS256", url="")

    @app.post("/test")
    async def get_test(auth: TenantData = Depends(tenant)):
        return auth.dict()

    test_client = TestClient(app)
    yield test_client


@pytest.fixture
def token_mock_rs256():
    payload = {
        "sub": "901",
        "realm_access": {"roles": ["role-annotator"]},
        "tenants": ["tenant1", "epam"],
    }

    token = create_access_token(
        data=payload, secret=private_key, expires_delta=15, algorithm="RS256"
    )
    yield token


@pytest.fixture
def client_token_mock_rs256():
    payload = {
        "sub": "3855eb45-2c11-4b15-8989-257b3a51649c",
        "realm_access": {
            "roles": [
                "default-roles-master",
                "offline_access",
                "uma_authorization",
            ]
        },
        "clientId": "pipelines",
    }

    token = create_access_token(
        data=payload, secret=private_key, expires_delta=15, algorithm="RS256"
    )
    yield token


@pytest.fixture
def wrong_client_token_mock_rs256():
    payload = {
        "sub": "3855eb45-2c11-4b15-8989-257b3a51649c",
        "realm_access": {
            "roles": [
                "default-roles-master",
                "offline_access",
                "uma_authorization",
            ]
        },
        "clientId": "not_pipelines",
    }

    token = create_access_token(
        data=payload, secret=private_key, expires_delta=15, algorithm="RS256"
    )
    yield token


@pytest.fixture
def expired_token_mock_rs256():
    payload = {
        "sub": "901",
        "realm_access": {"roles": ["role-annotator"]},
        "tenants": ["tenant1", "epam"],
    }
    token = create_access_token(
        data=payload, secret=private_key, expires_delta=-15, algorithm="RS256"
    )
    yield token


@pytest.fixture
def wrong_data_token_mock_rs256():
    payload = {
        "sub": "901",
        "realm_access": {"roles": ["role-annotator"]},
        "qtenants": ["tenant1"],
    }
    token = create_access_token(
        data=payload, secret=private_key, expires_delta=15, algorithm="RS256"
    )
    yield token


@pytest.fixture
def token_mock_hs256():
    payload = {
        "sub": "901",
        "realm_access": {"roles": ["role-annotator"]},
        "tenants": ["tenant1", "epam"],
    }
    token = create_access_token(data=payload, secret=SECRET_KEY, expires_delta=15)
    yield token


@pytest.fixture
def expired_token_mock_hs256():
    payload = {
        "sub": "901",
        "realm_access": {"roles": ["role-annotator"]},
        "tenants": ["tenant1", "epam"],
    }
    token = create_access_token(data=payload, secret=SECRET_KEY, expires_delta=-15)
    yield token


@pytest.fixture
def wrong_data_token_mock_hs256():
    payload = {
        "sub": "901",
        "realm_access": {"roles": ["role-annotator"]},
        "qtenants": ["tenant1"],
    }
    token = create_access_token(data=payload, secret=SECRET_KEY, expires_delta=15)
    yield token


@pytest.fixture
def test_app_hs256(mock_jwk_client, mock_sig_key):
    app = FastAPI()
    tenant = get_tenant_info(key=SECRET_KEY, algorithm="HS256")

    @app.post("/test")
    async def get_test(auth: TenantData = Depends(tenant)):
        return auth.dict()

    test_client = TestClient(app)
    yield test_client
