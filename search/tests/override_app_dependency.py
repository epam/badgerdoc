"""
Module to override token dependency in fastapi.
Without overriding this dependency, it will
always make requests to
http://dev1.gcov.ru/auth/realms/master/protocol/openid-connect/certs
to get needed algorithm and check,
that given token is valid, not expired and
there are necessary tenants in token.
"""

from tenant_dependency import TenantData

from search.main import TOKEN, app

TEST_TOKEN = "token"
TEST_TENANT = "test"
TEST_HEADERS = {
    "X-Current-Tenant": TEST_TENANT,
    "Authorization": f"Bearer {TEST_TOKEN}",
}


def override():
    return TenantData(
        token=TEST_TOKEN, user_id="UUID", roles=["role"], tenants=[TEST_TENANT]
    )


app.dependency_overrides[TOKEN] = override
