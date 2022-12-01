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

HEADER_TENANT = "X-Current-Tenant"
TEST_TOKEN = "token"
TEST_TENANTS = "test", "other_tenant"
TEST_HEADER = {
    HEADER_TENANT: TEST_TENANTS[0],
    "Authorisation": f"Bearer {TEST_TOKEN}",
}
OTHER_TENANT_HEADER = {
    HEADER_TENANT: TEST_TENANTS[1],
    "Authorisation": f"Bearer {TEST_TOKEN}",
}


def override() -> TenantData:
    """Function to override tenant dependency for tests"""
    return TenantData(
        token=TEST_TOKEN, user_id="UUID", roles=["role"], tenants=TEST_TENANTS
    )
