"""
Module to override token dependency in fastapi.
Without overriding this dependency, it will
always make requests to
http://dev1.gcov.ru/auth/realms/master/protocol/openid-connect/certs
to get needed algorithm and check,
that given token is valid, not expired and
there are necessary tenants in token.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tenant_dependency import TenantData

from annotation.database import SQLALCHEMY_DATABASE_URL, get_db
from annotation.main import app
from annotation.microservice_communication.search import (
    AUTHORIZATION,
    BEARER,
    HEADER_TENANT,
)
from annotation.token_dependency import TOKEN
from annotation.utils import get_test_db_url

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

test_db_url = get_test_db_url(SQLALCHEMY_DATABASE_URL)
engine = create_engine(test_db_url)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSession()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
