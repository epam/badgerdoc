from typing import List

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from src import main
from src.routers import labelstudio


class TenantData(BaseModel):
    token: str
    user_id: str
    roles: List[str]
    tenants: List[str]


@pytest.fixture()
def setup_tenant():
    return TenantData(
        token="token",
        user_id="owner1",
        roles=["admin"],
        tenants=["tenant", "test"],
    )


@pytest.fixture
def test_app(setup_tenant):
    main.app.dependency_overrides[labelstudio.tenant] = lambda: setup_tenant
    yield TestClient(main.app)
