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

from app.main import app
from app.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from app.token_dependency import TOKEN

TEST_TOKEN = "token"
TEST_TENANT = "test"
TEST_HEADERS = {
    HEADER_TENANT: TEST_TENANT,
    AUTHORIZATION: f"{BEARER} {TEST_TOKEN}",
}


def override():
    return TenantData(
        token=TEST_TOKEN, user_id="UUID", roles=["role"], tenants=[TEST_TENANT]
    )


app.dependency_overrides[TOKEN] = override
