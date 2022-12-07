from contextlib import contextmanager
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from tenant_dependency import TenantData

import src.keycloak.schemas as kc_schemas
from src.main import app, check_authorization, tenant

client = TestClient(app)

token = {"access_token": "token", "token_type": "Bearer"}
token_schema = kc_schemas.TokenResponse.parse_obj(token)
data = {
    "username": "username",
    "password": "password",
    "grant_type": "password",
}

token_representation = {
    "access_token": "token",
    "expires_in": None,
    "id_token": None,
    "not-before-policy": None,
    "refresh_expires_in": None,
    "refresh_token": None,
    "scope": None,
    "session_state": None,
    "token_type": "Bearer",
}

mock_tenant_data = TenantData(
    token="token", user_id="user_id", roles=["admin"], tenants=["tenant"]
)


async def override_auth_token():
    return mock_tenant_data


app.dependency_overrides[tenant] = override_auth_token


user_1 = kc_schemas.User(id="1", username="user")
user_2 = kc_schemas.User(id="2", username="u__r")
user_3 = kc_schemas.User(id="3", username="hx")
mock_all_users = [user_1, user_2, user_3]
mock_users_with_role = [user_2, user_3]


@pytest.fixture()
def user_representation():
    def user_body(email=None, user_id=None, user_name=None):
        return {
            "access": None,
            "attributes": None,
            "clientConsents": None,
            "clientRoles": None,
            "createdTimestamp": None,
            "credentials": None,
            "disableableCredentialTypes": None,
            "email": email,
            "emailVerified": None,
            "enabled": None,
            "federatedIdentities": None,
            "federationLink": None,
            "firstName": None,
            "groups": None,
            "id": user_id,
            "lastName": None,
            "notBefore": None,
            "origin": None,
            "realmRoles": None,
            "requiredActions": None,
            "self": None,
            "serviceAccountClientId": None,
            "username": user_name,
        }

    return user_body


@contextmanager
def does_not_raise():
    yield


@pytest.mark.parametrize(
    "mock_tenant_data",
    [
        TenantData(
            token="token",
            user_id="user_id",
            roles=["admin"],
            tenants=["tenant"],
        ),
        TenantData(
            token="token", user_id="user_id", roles=[], tenants=["tenant"]
        ),
    ],
)
def test_check_authorization_role_is_missing(mock_tenant_data):
    with pytest.raises(HTTPException):
        check_authorization(token=mock_tenant_data, role="wrong_role")


def test_check_authorization_role_is_missing_status_code():
    with pytest.raises(HTTPException) as error_info:
        check_authorization(token=mock_tenant_data, role="wrong_role")
    assert error_info.value.status_code == 403


def test_check_authorization_role_is_missing_message():
    with pytest.raises(HTTPException) as error_info:
        check_authorization(token=mock_tenant_data, role="wrong_role")
    assert error_info.value.detail == "Access denied"


@pytest.mark.parametrize(
    "mock_tenant_data",
    [
        TenantData(
            token="token",
            user_id="user_id",
            roles=["role"],
            tenants=["tenant"],
        ),
        TenantData(
            token="token",
            user_id="user_id",
            roles=["some_role", "role"],
            tenants=["tenant"],
        ),
    ],
)
def test_check_authorization_role_is_right(mock_tenant_data):
    with does_not_raise():
        check_authorization(token=mock_tenant_data, role="role")


@patch("src.keycloak.query.get_token_v2", return_value=token_schema)
def test_login_body(token_schema):
    response = client.post(
        "/token",
        data={
            "username": "username",
            "password": "password",
            "grant_type": "password",
        },
    )
    assert response.json() == token_representation


@patch("src.keycloak.query.get_token_v2", return_value=token_schema)
@pytest.mark.parametrize(
    ("request_body", "status_code"),
    [
        (
            {
                "username": "username",
                "password": "password",
                "grant_type": "password",
            },
            200,
        ),
        (
            {
                "wrong_field": "username",
                "password": "password",
                "grant_type": "password",
            },
            422,
        ),
        (
            {
                "username": "username",
                "wrong_field": "password",
                "grant_type": "password",
            },
            422,
        ),
        (
            {
                "username": "username",
                "password": "password",
                "wrong_field": "password",
            },
            422,
        ),
        (
            {
                "username": "username",
                "password": "password",
                "grant_type": "wrong_value",
            },
            422,
        ),
        (
            {},
            422,
        ),
    ],
)
def test_login_status_code(token_schema, request_body, status_code):
    response = client.post("/token", data=request_body)
    assert response.status_code == status_code


@patch("src.keycloak.query.get_user", return_value=user_1)
class TestGetUserGWT:
    def test_get_user_jwt_body(self, mock_user, user_representation):
        response = client.get("/users/current")
        assert response.json() == user_representation(
            user_id="1", user_name="user"
        )

    def test_get_user_jwt_status_code(self, mock_user):
        response = client.get("/users/current")
        assert response.status_code == 200


@patch("src.keycloak.query.get_user", return_value=user_1)
class TestGetUser:
    def test_get_user_body(self, mock_user, user_representation):
        response = client.get("/users/user-id")
        assert response.json() == user_representation(
            user_id="1", user_name="user"
        )

    def test_get_user_status_code(self, mock_user):
        response = client.get("/users/user-id")
        assert response.status_code == 200


def test_get_user_info_from_token_introspection(
    mocked_token1, mocked_token1_data
):
    with patch(
        "src.keycloak.query.introspect_token", return_value=mocked_token1_data
    ):
        response = client.get(
            "/users/current_v2",
            headers={"Authorization": f"Bearer {mocked_token1}"},
        )
        assert response.json() == mocked_token1_data


group_1 = kc_schemas.Group(name="group_1")
group_2 = kc_schemas.Group(name="group_2")
mock_all_groups = [group_1, group_2]


@patch("src.keycloak.query.get_groups", return_value=mock_all_groups)
class TestGetTenants:
    def test_get_tenants_body(self, mock_groups):
        response = client.get("/tenants")
        assert response.json() == ["group_1", "group_2"]

    def test_get_tenants_status_code(self, mock_groups):
        response = client.get("/tenants")
        assert response.status_code == 200


@patch("src.keycloak.query.create_group", return_value=None)
@patch("src.s3.create_bucket", return_value=None)
class TestCreateTenant:
    def test_create_tenant_body(self, mock_group, mock_bucket):
        response = client.post("/tenants?tenant=tenant")
        assert response.json() == {"detail": "Tenant has been created"}

    @pytest.mark.parametrize(
        ("query_param", "response_status_code"),
        [
            ("?tenant=tenant", 201),
            ("?tenant=1", 422),
            ("?Tenant=1", 422),
            ("?tenant=", 422),
            ("?tenant=_tenant", 422),
            ("?tenant=ten_ant", 422),
            ("tenant=tenant", 404),
            ("", 422),
            ("?", 422),
        ],
    )
    def test_create_tenant_status_code(
        self, mock_group, mock_bucket, query_param, response_status_code
    ):
        response = client.post(f"/tenants{query_param}")
        assert response.status_code == response_status_code


@patch("src.keycloak.query.get_groups", return_value=mock_all_groups)
@patch("src.keycloak.query.get_user", return_value=user_1)
@patch("src.keycloak.schemas.User.add_tenant", return_value=None)
@patch("src.keycloak.query.update_user", return_value=None)
class TestAddUserToTenant:
    @pytest.mark.parametrize(
        ("tenant", "expected_result"),
        [
            ("group_1", {"detail": "User has been added to the tenant"}),
            ("group", {"detail": "Tenant not found"}),
        ],
    )
    def test_add_user_to_tenant1(
        self,
        mock_groups,
        mock_user,
        add_tenant,
        update_user,
        tenant,
        expected_result,
    ):
        response = client.put(f"/tenants/{tenant}/users/user_1")
        assert response.json() == expected_result

    @pytest.mark.parametrize(
        ("tenant", "expected_result"),
        [
            ("group_1", 200),
            ("group", 404),
        ],
    )
    def test_add_user_to_tenant2(
        self,
        mock_groups,
        mock_user,
        add_tenant,
        update_user,
        tenant,
        expected_result,
    ):
        response = client.put(f"/tenants/{tenant}/users/user_1")
        assert response.status_code == expected_result


@patch("src.keycloak.query.get_user", return_value=user_1)
@patch("src.keycloak.query.update_user", return_value=None)
@pytest.mark.parametrize(
    ("tenant", "expected_result"),
    [
        ("group_1", {"detail": "User has been removed from the tenant"}),
    ],
)
def test_remove_user_from_tenant_body(
    mock_user, update_user, tenant, expected_result
):
    response = client.delete(f"/tenants/{tenant}/users/user_1")
    assert response.json() == expected_result


@patch("src.keycloak.query.get_user", return_value=user_1)
@patch("src.keycloak.query.update_user", return_value=None)
@pytest.mark.parametrize(
    ("tenant", "expected_result"),
    [
        ("group_1", {"detail": "User has been removed from the tenant"}),
    ],
)
def test_remove_user_from_tenant_status_code(
    mock_user, update_user, tenant, expected_result
):
    response = client.delete(f"/tenants/{tenant}/users/user_1")
    assert response.status_code == 200


@patch("src.keycloak.query.get_users_v2", return_value=mock_all_users)
@patch(
    "src.keycloak.query.get_users_by_role", return_value=mock_users_with_role
)
class TestUsersSearch:
    @pytest.mark.parametrize("request_body", [{}, {"filters": []}])
    def test_get_all_users_body(
        self,
        mock_all_users,
        mock_users_with_role,
        request_body,
        user_representation,
    ):
        response = client.post("/users/search", json=request_body)
        assert response.json() == [
            user_representation(user_id="1", user_name="user"),
            user_representation(user_id="2", user_name="u__r"),
            user_representation(user_id="3", user_name="hx"),
        ]

    @pytest.mark.parametrize("request_body", [{}, {"filters": []}])
    def test_get_all_users_status_code(
        self, mock_all_users, mock_users_with_role, request_body
    ):
        response = client.post("/users/search", json=request_body)
        assert response.status_code == 200

    def test_filter_users_by_name_body(
        self, mock_all_users, mock_users_with_role, user_representation
    ):
        response = client.post(
            "/users/search",
            json={
                "filters": [
                    {"field": "name", "operator": "like", "value": "r"}
                ]
            },
        )
        assert response.json() == [
            user_representation(user_id="1", user_name="user"),
            user_representation(user_id="2", user_name="u__r"),
        ]

    def test_filter_users_by_name_status_code(
        self, mock_all_users, mock_users_with_role, user_representation
    ):
        response = client.post(
            "/users/search",
            json={
                "filters": [
                    {"field": "name", "operator": "like", "value": "r"}
                ]
            },
        )
        assert response.status_code == 200

    def test_filter_users_by_name_when_name_does_not_exist_body(
        self, mock_all_users, mock_users_with_role, user_representation
    ):
        response = client.post(
            "/users/search",
            json={
                "filters": [
                    {
                        "field": "name",
                        "operator": "like",
                        "value": "wrong_name",
                    }
                ]
            },
        )
        assert response.json() == []

    def test_filter_users_by_name_when_name_does_not_exist_status_code(
        self, mock_all_users, mock_users_with_role, user_representation
    ):
        response = client.post(
            "/users/search",
            json={
                "filters": [
                    {
                        "field": "name",
                        "operator": "like",
                        "value": "wrong_name",
                    }
                ]
            },
        )
        assert response.status_code == 200

    def test_filter_users_by_empty_name_status_code(
        self, mock_all_users, mock_users_with_role, user_representation
    ):
        response = client.post(
            "/users/search",
            json={
                "filters": [{"field": "name", "operator": "like", "value": ""}]
            },
        )
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "request_body",
        [
            {
                "filters": [
                    {"field": "id", "operator": "in", "value": ["1", "2"]}
                ]
            },
            {
                "filters": [
                    {
                        "field": "id",
                        "operator": "in",
                        "value": ["1", "2", "wrong_id"],
                    }
                ]
            },
        ],
    )
    def test_filter_users_by_id_body(
        self,
        mock_all_users,
        mock_users_with_role,
        user_representation,
        request_body,
    ):
        response = client.post(
            "/users/search",
            json=request_body,
        )

        assert response.json() == [
            user_representation(user_id="1", user_name="user"),
            user_representation(user_id="2", user_name="u__r"),
        ]

    @pytest.mark.parametrize(
        "request_body",
        [
            {
                "filters": [
                    {"field": "id", "operator": "in", "value": ["1", "2"]}
                ]
            },
            {
                "filters": [
                    {
                        "field": "id",
                        "operator": "in",
                        "value": ["1", "2", "wrong_id"],
                    }
                ]
            },
        ],
    )
    def test_filter_users_by_id_status_code(
        self,
        mock_all_users,
        mock_users_with_role,
        user_representation,
        request_body,
    ):
        response = client.post(
            "/users/search",
            json=request_body,
        )
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "request_body",
        [
            {"filters": [{"field": "id", "operator": "in", "value": []}]},
            {
                "filters": [
                    {"field": "id", "operator": "in", "value": ["wrong_id"]}
                ]
            },
        ],
    )
    def test_filter_users_by_wrong_or_empty_id_body(
        self,
        mock_all_users,
        mock_users_with_role,
        user_representation,
        request_body,
    ):
        response = client.post(
            "/users/search",
            json=request_body,
        )
        assert response.json() == []

    @pytest.mark.parametrize(
        "request_body",
        [
            {"filters": [{"field": "id", "operator": "in", "value": []}]},
            {
                "filters": [
                    {"field": "id", "operator": "in", "value": ["wrong_id"]}
                ]
            },
        ],
    )
    def test_filter_users_by_wrong_or_empty_id_status_code(
        self,
        mock_all_users,
        mock_users_with_role,
        user_representation,
        request_body,
    ):
        response = client.post(
            "/users/search",
            json={
                "filters": [
                    {"field": "id", "operator": "in", "value": ["wrong_id"]}
                ]
            },
        )
        assert response.status_code == 200

    def test_filter_users_by_role_body(
        self, mock_all_users, mock_users_with_role, user_representation
    ):
        response = client.post(
            "/users/search",
            json={
                "filters": [
                    {
                        "field": "role",
                        "operator": "eq",
                        "value": "role-annotator",
                    }
                ]
            },
        )
        assert response.json() == [
            user_representation(user_id="2", user_name="u__r"),
            user_representation(user_id="3", user_name="hx"),
        ]

    def test_filter_users_by_role_status_code(
        self, mock_all_users, mock_users_with_role, user_representation
    ):
        response = client.post(
            "/users/search",
            json={
                "filters": [
                    {
                        "field": "role",
                        "operator": "eq",
                        "value": "role-annotator",
                    }
                ]
            },
        )
        assert response.status_code == 200

    def test_filter_users_by_wrong_role_body(
        self, mock_all_users, mock_users_with_role, user_representation
    ):
        response = client.post(
            "/users/search",
            json={
                "filters": [
                    {"field": "role", "operator": "eq", "value": "wrong_role"}
                ]
            },
        )
        assert response.status_code == 422

    def test_filter_users_by_all_filters_body(
        self, mock_all_users, mock_users_with_role, user_representation
    ):
        response = client.post(
            "/users/search",
            json={
                "filters": [
                    {"field": "name", "operator": "like", "value": "u"},
                    {"field": "id", "operator": "in", "value": ["2"]},
                    {
                        "field": "role",
                        "operator": "eq",
                        "value": "role-annotator",
                    },
                ]
            },
        )
        assert response.json() == [
            user_representation(user_id="2", user_name="u__r"),
        ]

    def test_filter_users_by_all_filters_status_code(
        self, mock_all_users, mock_users_with_role, user_representation
    ):
        response = client.post(
            "/users/search",
            json={
                "filters": [
                    {"field": "name", "operator": "like", "value": "u"},
                    {"field": "id", "operator": "in", "value": ["2"]},
                    {
                        "field": "role",
                        "operator": "eq",
                        "value": "role-annotator",
                    },
                ]
            },
        )
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "request_body",
        [
            {
                "filters": [
                    {
                        "field": "name",
                        "operator": "like",
                        "value": "wrong_name",
                    },
                    {"field": "id", "operator": "in", "value": ["2"]},
                    {
                        "field": "role",
                        "operator": "eq",
                        "value": "role-annotator",
                    },
                ]
            },
            {
                "filters": [
                    {"field": "name", "operator": "like", "value": "u"},
                    {"field": "id", "operator": "in", "value": ["wrong_id"]},
                    {
                        "field": "role",
                        "operator": "eq",
                        "value": "role-annotator",
                    },
                ]
            },
        ],
    )
    def test_filter_users_by_all_filters_when_user_does_not_exist_body(
        self,
        mock_all_users,
        mock_users_with_role,
        request_body,
        user_representation,
    ):
        response = client.post(
            "/users/search",
            json=request_body,
        )
        assert response.json() == []

    @pytest.mark.parametrize(
        "request_body",
        [
            {
                "filters": [
                    {
                        "field": "name",
                        "operator": "like",
                        "value": "wrong_name",
                    },
                    {"field": "id", "operator": "in", "value": ["2"]},
                    {
                        "field": "role",
                        "operator": "eq",
                        "value": "role-annotator",
                    },
                ]
            },
            {
                "filters": [
                    {"field": "name", "operator": "like", "value": "u"},
                    {"field": "id", "operator": "in", "value": ["wrong_id"]},
                    {
                        "field": "role",
                        "operator": "eq",
                        "value": "role-annotator",
                    },
                ]
            },
        ],
    )
    def test_filter_users_by_all_filters_when_user_does_not_exist_body2(
        self,
        mock_all_users,
        mock_users_with_role,
        request_body,
        user_representation,
    ):
        response = client.post(
            "/users/search",
            json=request_body,
        )
        assert response.status_code == 200


user = kc_schemas.User(email="mail@mail.ru", id="1", username="user")
mock_users = [user]


@patch("src.keycloak.query.create_user", return_value=None)
@patch("src.keycloak.query.get_users_v2", return_value=mock_all_users)
@patch("src.keycloak.query.execute_action_email", return_value=None)
class TestUserRegistration:
    def test_user_registration_body(self, user, mock_all_users, action_email):
        response = client.post("/users/registration?email=mail@mail.ru")
        assert response.json() == {"detail": "User has been created"}

    @pytest.mark.parametrize(
        ("query", "response_status_code"),
        [
            ("", 422),
            ("?", 422),
            ("?email=", 400),
            ("?email=mail", 400),
            ("?email=mail@", 400),
            ("?email=mail@mail", 400),
            ("?email=mail@mail.ru1", 400),
            ("?email=mail@ma^il.ru", 400),
            ("?email=mail@mail.ru", 201),
        ],
    )
    def test_user_registration_body_status_code(
        self, user, mock_all_users, action_email, query, response_status_code
    ):
        response = client.post(f"/users/registration{query}")
        assert response.status_code == response_status_code


def test_get_idp_names_and_SSOauth_links(
    mocked_admin_auth_data, mocked_identity_providers_data
):
    with patch(
        "src.keycloak.query.get_master_realm_auth_data",
        return_value=mocked_admin_auth_data,
    ), patch(
        "src.keycloak.query.get_identity_providers_data",
        return_value=mocked_identity_providers_data,
    ):
        response = client.get("/identity_providers_data")
        assert response.json() == {
            "Identity Providers Info": [
                {
                    "Alias": "EPAM_SSO",
                    "Auth link": "http://dev2.badgerdoc.com/auth/realms/master/protocol/openid-connect/auth?client_id=BadgerDoc&response_type=token&redirect_uri=http://dev2.badgerdoc.com/login&kc_idp_hint=EPAM_SSO",  # noqa: E501
                }
            ]
        }
