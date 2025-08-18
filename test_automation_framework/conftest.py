import pytest
from settings import load_settings
from helpers.auth.auth_service import AuthService
from helpers.base_client.base_client import BaseClient


@pytest.fixture(scope="session")
def base_client(settings):
    client = BaseClient(settings.BASE_URL, timeout=10)
    yield client
    client.close()


@pytest.fixture(scope="session")
def auth_service(base_client) -> AuthService:
    return AuthService(base_client)


@pytest.fixture(scope="session")
def auth_token(auth_service, settings) -> tuple[str, str]:
    return auth_service.get_token(
        settings.API_USER, settings.API_PASS.get_secret_value()
    )


@pytest.fixture(scope="session")
def settings():
    return load_settings()
