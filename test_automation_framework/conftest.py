import pytest
from settings import load_settings
from helpers.auth.auth_service import AuthService
from helpers.base_client.base_client import BaseClient
import logging
from helpers.datasets.dataset_client import DatasetClient
from logging import getLogger


logger = getLogger(__name__)


def pytest_configure(config):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


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
    return auth_service.get_token(settings.API_USER, settings.API_PASS.get_secret_value())


@pytest.fixture(scope="session")
def settings():
    return load_settings()


@pytest.fixture(scope="session")
def tenant():
    return "demo-badgerdoc"


@pytest.fixture(scope="session")
def dataset_tracker(auth_token, settings, tenant):
    access_token, _ = auth_token

    client = DatasetClient(settings.BASE_URL, access_token, tenant)
    created = []

    yield created, client

    # cleanup step
    for name in created:
        try:
            resp = client.delete_dataset(name=name)
            logger.info(f"[dataset_tracker] Deleted dataset {name}: {resp['detail']}")
        except Exception as e:
            logger.warning(f"[dataset_tracker] Failed to delete dataset {name}: {e}")
