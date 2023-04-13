from typing import Generator, List

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from convert import main
from convert.routers import labelstudio


class TenantData(BaseModel):
    token: str
    user_id: str
    roles: List[str]
    tenants: List[str]


@pytest.fixture()
def setup_tenant() -> TenantData:
    return TenantData(
        token="token",
        user_id="owner1",
        roles=["admin"],
        tenants=["tenant", "test"],
    )


@pytest.fixture
def test_app(setup_tenant: TenantData) -> Generator[TestClient, None, None]:
    main.app.dependency_overrides[labelstudio.tenant] = lambda: setup_tenant
    yield TestClient(main.app)
