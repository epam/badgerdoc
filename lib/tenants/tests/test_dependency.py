from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from src.dependency import (
    get_tenant_info,
    TenantData,
    TenantDependencyBase,
    TenantDependencyDocs,
)
from usage_example.jwt_generator import create_access_token

SECRET_KEY = "testsecretkey"

app = FastAPI()
tenant = get_tenant_info(SECRET_KEY, "HS256")


@app.post("/test")
async def get_test(auth: TenantData = Depends(tenant)):
    return auth.dict()


test_client = TestClient(app)


def test_dependency_positive():
    payload = {
        "user_id": 901,
        "tenant": "merck",
        "roles": ["admin", "ml engineer", "devops"],
    }
    token = create_access_token(
        data=payload, secret=SECRET_KEY, expires_delta=15
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = test_client.post("/test", headers=headers)
    assert res.status_code == 200
    assert res.json() == payload


def test_dependency_expired_token():
    payload = {
        "user_id": 901,
        "roles": ["admin", "ml engineer", "devops"],
        "tenant": "merck",
    }
    token = create_access_token(
        data=payload, secret=SECRET_KEY, expires_delta=-15
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = test_client.post("/test", headers=headers)
    assert res.status_code == 401
    assert res.json() == {"detail": "Token is expired!"}


def test_dependency_invalid_token():
    headers = {"Authorization": "Bearer does not exist"}
    res = test_client.post("/test", headers=headers)
    assert res.status_code == 401
    assert res.json() == {"detail": "Token is invalid!"}


def test_dependency_wrong_data():
    payload = {
        "some": 901,
        "users": ["admin", "ml engineer", "devops"],
        "1tenants": "merck",
    }
    token = create_access_token(
        data=payload, secret=SECRET_KEY, expires_delta=15
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = test_client.post("/test", headers=headers)
    assert res.status_code == 403
    assert res.json() == {"detail": "Wrong data provided in jwt!"}


def test_tenant_class_generator():
    docs_dep = get_tenant_info("key", "algorithm", debug=True)
    assert isinstance(docs_dep, TenantDependencyDocs)
    base_dep = get_tenant_info("key", "algorithm")
    assert isinstance(base_dep, TenantDependencyBase)
