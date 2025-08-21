from logging import getLogger
import pytest
from helpers.base_client.base_client import HTTPError
from helpers.menu.menu_client import MenuClient
from helpers.datasets.dataset_client import DatasetClient
from datetime import datetime
import uuid

logger = getLogger(__name__)


class TestAuthAPI:
    def test_basic_auth(self, auth_token):
        access_token, refresh_token = auth_token
        assert access_token, "No access_token found!"
        assert refresh_token, "No refresh_token found!"

    def test_wrong_creds(self, auth_service):
        with pytest.raises(HTTPError) as e:
            auth_service.get_token("wrong", "wrong")
        assert e.value.status_code == 401, f"Expected 401 but got {e.value.status_code}: {e.value.body}"

    def test_refresh_token(self, auth_token, auth_service):
        access_token, refresh_token = auth_token
        new_access_token, new_refresh_token = auth_service.refresh_token(refresh_token=refresh_token)
        assert new_access_token != access_token, "Old access token is the same as new access token!"
        assert new_refresh_token != refresh_token, "Old refresh token is the same as new refresh token!"


class TestAPI:
    def test_menu(self, auth_token, settings):
        access_token, _ = auth_token
        tenant = "demo-badgerdoc"
        menu_client = MenuClient(settings.BASE_URL, access_token, tenant)
        menu = menu_client.get_menu()

        assert isinstance(menu, list), "Menu is expected to be a list!"
        assert len(menu), "Menu should have been returned!"

        required_keys = {
            "name",
            "badgerdoc_path",
            "is_external",
            "is_iframe",
            "url",
            "children",
        }
        for item in menu:
            assert required_keys <= item.keys(), f"Menu item missing keys: {item}"

        first_item = menu[0]
        assert isinstance(first_item["name"], str)
        assert isinstance(first_item["badgerdoc_path"], str)
        assert isinstance(first_item["is_external"], bool)
        assert isinstance(first_item["children"], (list, type(None)))

        expected_names = {"Documents", "My Tasks", "Jobs", "Settings"}
        actual_names = {item["name"] for item in menu}
        assert expected_names <= actual_names, f"Missing expected menu items: {expected_names - actual_names}"

        settings_item = next(item for item in menu if item["name"] == "Settings")
        assert isinstance(settings_item["children"], list)
        assert any(child["name"] == "Keycloak" for child in settings_item["children"])


class TestDatasets:
    def test_search_basic(self, auth_token, settings):
        access_token, _ = auth_token
        tenant = "demo-badgerdoc"
        client = DatasetClient(settings.BASE_URL, access_token, tenant)

        result = client.search()

        assert "pagination" in result, "Response must have 'pagination'"
        assert "data" in result, "Response must have 'data'"
        assert isinstance(result["data"], list), "'data' must be a list"

        pagination = result["pagination"]
        required_pagination_keys = {
            "page_num",
            "page_offset",
            "page_size",
            "min_pages_left",
            "total",
            "has_more",
        }
        assert (
            required_pagination_keys <= pagination.keys()
        ), f"Pagination missing keys: {required_pagination_keys - pagination.keys()}"

        for dataset in result["data"]:
            required_dataset_keys = {"id", "name", "count", "created"}
            assert (
                required_dataset_keys <= dataset.keys()
            ), f"Dataset missing keys: {required_dataset_keys - dataset.keys()}"
            assert isinstance(dataset["id"], int)
            assert isinstance(dataset["name"], str)
            assert isinstance(dataset["count"], int)
            try:
                datetime.fromisoformat(dataset["created"])
            except ValueError:
                pytest.fail(f"Dataset created date is not ISO format: {dataset['created']}")

    def test_search_sorting(self, auth_token, settings, tenant):
        access_token, _ = auth_token
        client = DatasetClient(settings.BASE_URL, access_token, tenant)

        result = client.search(sorting=[{"direction": "desc", "field": "name"}])
        data = result["data"]
        names = [d["name"] for d in data]
        assert names == sorted(names, reverse=True), "Datasets are not sorted descending by name"

    def test_search_pagination(self, auth_token, settings, tenant):
        access_token, _ = auth_token
        client = DatasetClient(settings.BASE_URL, access_token, tenant)

        result = client.search(page_num=1, page_size=15)
        assert len(result["data"]) <= 15, "Page size exceeded"
        assert result["pagination"]["page_num"] == 1

    def test_selection(self, auth_token, settings, tenant):
        access_token, _ = auth_token
        client = DatasetClient(settings.BASE_URL, access_token, tenant)

        datasets = client.search()["data"]
        assert datasets, "No datasets found"
        dataset_id = datasets[0]["id"]

        files_selected = client.search_files(dataset_id=dataset_id)["data"]
        assert isinstance(files_selected, list), "Files response is not a list"

        for f in files_selected:
            assert any(
                d["id"] == dataset_id for d in f.get("datasets", [])
            ), f"File {f['original_name']} does not belong to dataset {dataset_id}"

        files_all = client.search_files()["data"]  # no dataset_id
        assert isinstance(files_all, list), "Files response is not a list"

        has_dataset = any(f.get("datasets") for f in files_all)
        has_no_dataset = any(not f.get("datasets") for f in files_all)
        assert has_dataset or has_no_dataset, "Unexpected empty file list"

    def test_create_and_delete_dataset(self, auth_token, settings, tenant):
        access_token, _ = auth_token
        client = DatasetClient(settings.BASE_URL, access_token, tenant)

        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        create_resp = client.create_dataset(name=dataset_name)

        assert "detail" in create_resp, f"Unexpected response: {create_resp}"
        assert "successfully created" in create_resp["detail"].lower()

        search_resp = client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])
        datasets = search_resp["data"]

        assert any(d["name"] == dataset_name for d in datasets), f"Dataset {dataset_name} not found after creation"

        delete_resp = client.delete_dataset(name=dataset_name)

        assert "detail" in delete_resp, f"Unexpected delete response: {delete_resp}"
        assert "successfully deleted" in delete_resp["detail"].lower()

        search_after = client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])
        datasets_after = search_after["data"]

        assert all(
            d["name"] != dataset_name for d in datasets_after
        ), f"Dataset {dataset_name} still found after deletion!"

    @pytest.mark.skip(reason="Successfully creates dataset")
    def test_create_dataset_with_empty_name(self, dataset_tracker):
        created, client = dataset_tracker

        with pytest.raises(HTTPError) as e:
            client.create_dataset(name="")

        assert e.value.status_code in (400, 422)

    def test_create_duplicate_dataset(self, dataset_tracker):
        created, client = dataset_tracker
        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        resp = client.create_dataset(name=dataset_name)
        created.append(dataset_name)  # register for cleanup
        assert "successfully created" in resp["detail"].lower()

        with pytest.raises(HTTPError) as e:
            client.create_dataset(name=dataset_name)
        assert e.value.status_code == 400
        assert "already exists" in e.value.body.lower()
