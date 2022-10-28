import pytest


from pydantic import ValidationError
from src.schema import TenantData


@pytest.mark.parametrize(
    ("user_id", "roles", "tenant", "expected_result"),
    [
        (
            901,
            ["admin", "ml engineer", "devops"],
            "merck",
            {
                "user_id": 901,
                "tenant": "merck",
                "roles": ["admin", "ml engineer", "devops"],
            },
        ),
        (
            0,
            ["guest"],
            "merck",
            {"user_id": 0, "tenant": "merck", "roles": ["guest"]},
        ),
        (
            0,
            ["some"],
            "some",
            {"user_id": 0, "tenant": "some", "roles": ["some"]},
        ),
    ],
)
def test_tenant_data_positive(user_id, roles, tenant, expected_result):
    assert (
        TenantData(user_id=user_id, tenant=tenant, roles=roles).dict()
        == expected_result
    )


def tenant_data_negative():
    with pytest.raises(ValidationError):
        TenantData(user_id=None, tenant="merck", roles=["guest"])
    with pytest.raises(ValidationError):
        TenantData(user_id=1, tenant=None, roles=["admin"])
    with pytest.raises(ValidationError):
        TenantData(user_id=1, tenant="merck", roles=[])
