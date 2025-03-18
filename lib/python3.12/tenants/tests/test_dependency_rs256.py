from src.dependency import (
    TenantDependencyBase,
    TenantDependencyDocs,
    get_tenant_info,
)

CURRENT_TENANT = "tenant1"


def test_dependency_positive(token_mock_rs256, test_app_rs256):
    headers = {
        "Authorization": f"Bearer {token_mock_rs256}",
        "X-Current-Tenant": CURRENT_TENANT,
    }
    response_body = {
        "roles": ["role-annotator"],
        "tenants": ["tenant1", "epam"],
        "token": f"{token_mock_rs256}",
        "user_id": "901",
    }
    res = test_app_rs256.post("/test", headers=headers)
    assert res.status_code == 200
    assert res.json() == response_body


def test_dependency_expired_token(expired_token_mock_rs256, test_app_rs256):
    headers = {
        "Authorization": f"Bearer {expired_token_mock_rs256}",
        "X-Current-Tenant": CURRENT_TENANT,
    }
    res = test_app_rs256.post("/test", headers=headers)
    assert res.status_code == 401
    assert res.json() == {"detail": "Token is expired!"}


def test_dependency_invalid_token(test_app_rs256):
    headers = {
        "Authorization": "Bearer does not exist",
        "X-Current-Tenant": CURRENT_TENANT,
    }
    res = test_app_rs256.post("/test", headers=headers)
    assert res.status_code == 401
    assert res.json() == {"detail": "Token is invalid!"}


def test_dependency_wrong_data(wrong_data_token_mock_rs256, test_app_rs256):
    headers = {
        "Authorization": f"Bearer {wrong_data_token_mock_rs256}",
        "X-Current-Tenant": CURRENT_TENANT,
    }
    res = test_app_rs256.post("/test", headers=headers)
    assert res.status_code == 403
    assert res.json() == {"detail": "Wrong data provided in jwt!"}


def test_tenant_class_generator():
    docs_dep = get_tenant_info(url="key", algorithm="RS256", debug=True)
    assert isinstance(docs_dep, TenantDependencyDocs)
    base_dep = get_tenant_info("key", "RS256")
    assert isinstance(base_dep, TenantDependencyBase)


def test_current_tenant_not_provided(token_mock_rs256, test_app_rs256):
    headers = {"Authorization": f"Bearer {token_mock_rs256}"}
    res = test_app_rs256.post("/test", headers=headers)
    assert res.status_code == 401
    assert res.json() == {"detail": "No X-Current-Tenant provided!"}


def test_current_tenant_wrong(token_mock_rs256, test_app_rs256):
    headers = {
        "Authorization": f"Bearer {token_mock_rs256}",
        "X-Current-Tenant": "wrong",
    }
    res = test_app_rs256.post("/test", headers=headers)
    assert res.status_code == 403
    assert res.json() == {"detail": "X-Current-Tenant not in jwt tenants!"}


def test_client_token_positive(client_token_mock_rs256, test_app_rs256):
    headers = {
        "Authorization": f"Bearer {client_token_mock_rs256}",
        "X-Current-Tenant": CURRENT_TENANT,
    }
    response_body = {
        "roles": [
            "default-roles-master",
            "offline_access",
            "uma_authorization",
        ],
        "tenants": [CURRENT_TENANT],
        "token": f"{client_token_mock_rs256}",
        "user_id": "3855eb45-2c11-4b15-8989-257b3a51649c",
    }
    res = test_app_rs256.post("/test", headers=headers)
    assert res.status_code == 200
    assert res.json() == response_body


def test_wrong_client_token_data(
    wrong_client_token_mock_rs256, test_app_rs256
):
    headers = {
        "Authorization": f"Bearer {wrong_client_token_mock_rs256}",
        "X-Current-Tenant": CURRENT_TENANT,
    }
    res = test_app_rs256.post("/test", headers=headers)
    assert res.status_code == 403
    assert res.json() == {"detail": "Wrong data provided in jwt!"}
