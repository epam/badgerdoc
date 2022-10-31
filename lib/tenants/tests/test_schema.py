import pytest


from pydantic import ValidationError
from src.schema import TenantData, SupportedAlgorithms


@pytest.mark.parametrize(
    ("token", "user_id", "roles", "tenants", "expected_result"),
    [
        (
            "token",
            "901",
            ["admin", "ml engineer", "devops"],
            ["merck"],
            {
                "token": "token",
                "user_id": "901",
                "roles": ["admin", "ml engineer", "devops"],
                "tenants": ["merck"],
            },
        ),
        (
            "token",
            "901",
            ["admin"],
            ["merck"],
            {
                "token": "token",
                "user_id": "901",
                "roles": ["admin"],
                "tenants": ["merck"],
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
        TenantData(user_id=None, tenant="merck", roles=["guest"])
    with pytest.raises(ValidationError):
        TenantData(user_id=1, tenant=None, roles=["admin"])
    with pytest.raises(ValidationError):
        TenantData(user_id=1, tenant="merck", roles=[])


def test_enum_members():
    assert SupportedAlgorithms.members() == [
        SupportedAlgorithms.HS256,
        SupportedAlgorithms.RS256,
    ]
