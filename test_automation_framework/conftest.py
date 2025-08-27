import logging
from logging import getLogger
from typing import Tuple

import pytest

from settings import load_settings
from helpers.auth.auth_service import AuthService
from helpers.base_client.base_client import BaseClient
from helpers.datasets.dataset_client import DatasetClient
from helpers.files.file_client import FileClient
from helpers.jobs.jobs_client import JobsClient
from helpers.menu.menu_client import MenuClient
from helpers.users.users import UsersClient
from helpers.reports.reports_client import ReportsClient

logger = getLogger(__name__)


def pytest_configure():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@pytest.fixture(scope="session")
def settings():
    return load_settings()


@pytest.fixture(scope="session")
def tenant(settings) -> str:
    return getattr(settings, "TENANT", "demo-badgerdoc")


@pytest.fixture(scope="session")
def base_client(settings) -> BaseClient:
    client = BaseClient(settings.BASE_URL, timeout=10)
    yield client
    client.close()


@pytest.fixture(scope="session")
def auth_service(base_client) -> AuthService:
    return AuthService(base_client)


@pytest.fixture(scope="session")
def auth_token(auth_service, settings) -> Tuple[str, str]:
    return auth_service.get_token(settings.API_USER, settings.API_PASS.get_secret_value())


@pytest.fixture
def access_token(auth_token) -> str:
    return auth_token[0]


@pytest.fixture
def menu_client(settings, access_token, tenant) -> MenuClient:
    return MenuClient(settings.BASE_URL, access_token, tenant)


@pytest.fixture
def dataset_client(settings, access_token, tenant) -> DatasetClient:
    return DatasetClient(settings.BASE_URL, access_token, tenant)


@pytest.fixture
def file_client(settings, access_token, tenant) -> FileClient:
    return FileClient(settings.BASE_URL, access_token, tenant)


@pytest.fixture
def jobs_client(settings, access_token, tenant) -> JobsClient:
    return JobsClient(settings.BASE_URL, access_token, tenant)


@pytest.fixture
def reports_client(settings, access_token, tenant) -> ReportsClient:
    return ReportsClient(settings.BASE_URL, access_token, tenant)


@pytest.fixture
def user_uuid(settings, access_token, tenant) -> str:
    users_client = UsersClient(settings.BASE_URL, access_token, tenant)
    users = users_client.search_users()
    return next((u.id for u in users if u.username == "admin"), None)


@pytest.fixture
def dataset_tracker(dataset_client):
    created: list[str] = []
    yield created, dataset_client
    for name in created:
        try:
            resp = dataset_client.delete_dataset(name=name)
            logger.info(f"[dataset_tracker] Deleted dataset {name}: {resp.get('detail')}")
        except Exception as e:
            logger.warning(f"[dataset_tracker] Failed to delete dataset {name}: {e}")


@pytest.fixture
def file_tracker(file_client):
    created_files: list[dict] = []
    yield created_files, file_client
    if created_files:
        ids = [f["id"] for f in created_files if f.get("id") is not None]
        if ids:
            try:
                result = file_client.delete_files(ids)
                logger.info(f"[file_tracker] Deleted files: {ids}, response={result}")
            except Exception as e:
                logger.warning(f"[file_tracker] Failed to cleanup files {ids}: {e}")


@pytest.fixture
def job_tracker(jobs_client):
    created: list[dict] = []
    yield created, jobs_client
    for job in created:
        job_id = job.get("id") or job.get("job_id") or (job.get("job") or {}).get("id")
        if not job_id:
            continue
        try:
            jobs_client.post("/jobs/jobs/cancel", json={"id": job_id}, headers=jobs_client._default_headers())
            logger.info(f"[job_tracker] Cancelled job {job_id}")
        except Exception as e:
            logger.warning(f"[job_tracker] Could not cancel job {job_id}: {e}")
