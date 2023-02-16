from typing import List

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from src import main
from src.routers import label_studio


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
def test_app(setup_tenant):
    main.app.dependency_overrides[label_studio.tenant] = lambda: setup_tenant
    client = TestClient(main.app)
    yield client
