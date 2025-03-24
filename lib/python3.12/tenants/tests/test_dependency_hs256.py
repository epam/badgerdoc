from src.dependency import (
    TenantDependencyBase,
    TenantDependencyDocs,
    get_tenant_info,
)

CURRENT_TENANT = "tenant1"


def test_dependency_positive(test_app_hs256, token_mock_hs256):
    headers = {
        "Authorization": f"Bearer {token_mock_hs256}",
        "X-Current-Tenant": CURRENT_TENANT,
    }
    response_body = {
        "roles": ["role-annotator"],
        "tenants": ["tenant1", "epam"],
        "token": f"{token_mock_hs256}",
        "user_id": "901",
    }
    res = test_app_hs256.post("/test", headers=headers)
    assert res.status_code == 200
    assert res.json() == response_body


def test_dependency_expired_token(test_app_hs256, expired_token_mock_hs256):
    headers = {
        "Authorization": f"Bearer {expired_token_mock_hs256}",
        "X-Current-Tenant": CURRENT_TENANT,
    }
    res = test_app_hs256.post("/test", headers=headers)
    assert res.status_code == 401
    assert res.json() == {"detail": "Token is expired!"}


def test_dependency_invalid_token(test_app_hs256):
    headers = {
        "Authorization": "Bearer does not exist",
        "X-Current-Tenant": CURRENT_TENANT,
    }
    res = test_app_hs256.post("/test", headers=headers)
    assert res.status_code == 401
    assert res.json() == {"detail": "Token is invalid!"}


def test_dependency_wrong_data(test_app_hs256, wrong_data_token_mock_hs256):
    headers = {
        "Authorization": f"Bearer {wrong_data_token_mock_hs256}",
        "X-Current-Tenant": CURRENT_TENANT,
    }
    res = test_app_hs256.post("/test", headers=headers)
    assert res.status_code == 403
    assert res.json() == {"detail": "Wrong data provided in jwt!"}


def test_tenant_class_generator():
    docs_dep = get_tenant_info("key", "HS256", debug=True)
    assert isinstance(docs_dep, TenantDependencyDocs)
    base_dep = get_tenant_info("key", "HS256")
    assert isinstance(base_dep, TenantDependencyBase)


def test_current_tenant_not_provided(test_app_hs256, token_mock_hs256):
    headers = {"Authorization": f"Bearer {token_mock_hs256}"}
    res = test_app_hs256.post("/test", headers=headers)
    assert res.status_code == 401
    assert res.json() == {"detail": "No X-Current-Tenant provided!"}


def test_current_tenant_wrong(test_app_hs256, token_mock_hs256):
    headers = {
        "Authorization": f"Bearer {token_mock_hs256}",
        "X-Current-Tenant": "wrong",
    }
    res = test_app_hs256.post("/test", headers=headers)
    assert res.status_code == 403
    assert res.json() == {"detail": "X-Current-Tenant not in jwt tenants!"}
