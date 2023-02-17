import pytest
from pydantic import ValidationError

from src.schema import SupportedAlgorithms, TenantData


@pytest.mark.parametrize(
    ("token", "user_id", "roles", "tenants", "expected_result"),
    [
        (
            "token",
            "901",
            ["admin", "ml engineer", "devops"],
            ["tenant1"],
            {
                "token": "token",
                "user_id": "901",
                "roles": ["admin", "ml engineer", "devops"],
                "tenants": ["tenant1"],
            },
        ),
        (
            "token",
            "901",
            ["admin"],
            ["tenant1"],
            {
                "token": "token",
                "user_id": "901",
                "roles": ["admin"],
                "tenants": ["tenant1"],
            },
        ),
    ],
)
def test_tenant_data_positive(token, user_id, roles, tenants, expected_result):
    assert (
        TenantData(
            token=token, user_id=user_id, roles=roles, tenants=tenants
        ).dict()
        == expected_result
    )


def tenant_data_negative():
    with pytest.raises(ValidationError):
        TenantData(user_id=None, tenant="tenant1", roles=["guest"])
    with pytest.raises(ValidationError):
        TenantData(user_id=1, tenant=None, roles=["admin"])
    with pytest.raises(ValidationError):
        TenantData(user_id=1, tenant="tenant1", roles=[])


def test_enum_members():
    assert SupportedAlgorithms.members() == [
        SupportedAlgorithms.HS256,
        SupportedAlgorithms.RS256,
    ]
