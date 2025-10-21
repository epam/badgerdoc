import logging
from logging import getLogger
from typing import Tuple
from playwright.sync_api import expect


import pytest

from settings import load_settings
from helpers.auth.auth_client import AuthClient
from helpers.base_client.base_client import BaseClient
from helpers.datasets.dataset_client import DatasetClient
from helpers.files.file_client import FileClient
from helpers.jobs.jobs_client import JobsClient
from helpers.menu.menu_client import MenuClient
from helpers.category.categories import CategoriesClient
from helpers.users.users import UsersClient
from helpers.reports.reports_client import ReportsClient
from helpers.plugins.plugins_client import PluginsClient

from playwright.sync_api import Page

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
    client = BaseClient(f"{settings.BASE_URL}:{settings.BASE_PORT}", timeout=10)
    yield client
    client.close()


@pytest.fixture(scope="session")
def auth_service(base_client) -> AuthClient:
    return AuthClient(base_client)


@pytest.fixture(scope="session")
def auth_token(auth_service, settings) -> Tuple[str, str]:
    return auth_service.get_token(settings.API_USER, settings.API_PASS.get_secret_value())


@pytest.fixture
def access_token(auth_token) -> str:
    return auth_token[0]


@pytest.fixture
def menu_client(settings, access_token, tenant) -> MenuClient:
    return MenuClient(f"{settings.BASE_URL}:{settings.BASE_PORT}", access_token, tenant)


@pytest.fixture
def dataset_client(settings, access_token, tenant) -> DatasetClient:
    return DatasetClient(f"{settings.BASE_URL}:{settings.BASE_PORT}", access_token, tenant)


@pytest.fixture
def file_client(settings, access_token, tenant) -> FileClient:
    return FileClient(f"{settings.BASE_URL}:{settings.BASE_PORT}", access_token, tenant)


@pytest.fixture
def jobs_client(settings, access_token, tenant) -> JobsClient:
    return JobsClient(f"{settings.BASE_URL}:{settings.BASE_PORT}", access_token, tenant)


@pytest.fixture
def reports_client(settings, access_token, tenant) -> ReportsClient:
    return ReportsClient(f"{settings.BASE_URL}:{settings.BASE_PORT}", access_token, tenant)


@pytest.fixture
def plugins_client(settings, access_token, tenant) -> PluginsClient:
    return PluginsClient(f"{settings.BASE_URL}:{settings.BASE_PORT}", access_token, tenant)


@pytest.fixture
def user_uuid(settings, access_token, tenant) -> str:
    users_client = UsersClient(f"{settings.BASE_URL}:{settings.BASE_PORT}", access_token, tenant)
    users = users_client.search_users()
    return next((u.id for u in users if u.username == "admin"), None)


@pytest.fixture
def categories_client(settings, access_token, tenant) -> CategoriesClient:
    return CategoriesClient(f"{settings.BASE_URL}:{settings.BASE_PORT}", access_token, tenant)


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


@pytest.fixture
def plugins_tracker(plugins_client):
    created: list[int] = []
    yield created, plugins_client
    for id in created:
        try:
            plugins_client.delete_plugin(plugin_id=id)
            logger.info(f"[plugins_tracker] Deleted plugin {id}")
        except Exception as e:
            logger.warning(f"[plugins_tracker] Failed to delete plugin {id}: {e}")


@pytest.fixture
def logged_in_page(page: Page, settings) -> Page:
    page.goto(f"{settings.BASE_URL}:8083/login", timeout=180000)
    page.get_by_role("textbox", name="Username").fill("admin")
    page.get_by_role("textbox", name="Password").fill("admin")
    page.get_by_role("button", name="Login", exact=True).click()
    items = page.locator("a[class^='document-card-view-item_card-item']")
    expect(items.first).to_be_visible(timeout=100000)
    return page


@pytest.fixture
def plugins_page(logged_in_page, settings) -> Page:
    page = logged_in_page
    page.goto(f"{settings.BASE_URL}:8083/settings/plugins")
    row_cells = page.locator("div[role='row'] div[role='cell']:first-child div div")
    expect(row_cells.first).to_be_visible(timeout=100000)
    return page


@pytest.fixture
def jobs_page(logged_in_page, settings) -> Page:
    page = logged_in_page
    page.goto(f"{settings.BASE_URL}:8083/jobs")
    rows = page.locator("div[role='row']").locator("xpath=..").locator("div[role='row']:not(.uui-table-header-row)")
    expect(rows.first).to_be_visible(timeout=5000)
    return page


@pytest.fixture
def categories_page(logged_in_page, settings) -> Page:
    page = logged_in_page
    page.goto(f"{settings.BASE_URL}:8083/categories")
    rows = page.locator("div[role='row']").locator("xpath=..").locator("div[role='row']:not(.uui-table-header-row)")
    expect(rows.first).to_be_visible(timeout=5000)
    return page


@pytest.fixture
def tasks_page(logged_in_page, settings) -> Page:
    page = logged_in_page
    page.goto(f"{settings.BASE_URL}:8083/my tasks")
    rows = page.locator("div[role='row']").locator("xpath=..").locator("div[role='row']:not(.uui-table-header-row)")
    expect(rows.first).to_be_visible(timeout=5000)
    return page
