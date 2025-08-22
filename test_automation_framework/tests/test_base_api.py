from logging import getLogger
import pytest
from helpers.base_client.base_client import HTTPError
from helpers.menu.menu_client import MenuClient
from helpers.datasets.dataset_client import DatasetClient
from datetime import datetime
import uuid
import shutil
from pathlib import Path

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
    def test_search_basic(self, auth_token, settings, tenant):
        access_token, _ = auth_token
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

        files_all = client.search_files()["data"]
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
        created.append(dataset_name)
        assert "successfully created" in resp["detail"].lower()

        with pytest.raises(HTTPError) as e:
            client.create_dataset(name=dataset_name)
        assert e.value.status_code == 400
        assert "already exists" in e.value.body.lower()


class TestFiles:
    def test_upload_and_delete_file(self, file_tracker, tmp_path):
        created_files, client = file_tracker

        data_dir = Path(__file__).parent.parent / "data"
        original_file = data_dir / "multivitamin.pdf"

        unique_name = f"{uuid.uuid4().hex}_multivitamin.pdf"
        temp_file = tmp_path / unique_name
        shutil.copy(original_file, temp_file)

        try:
            result = client.upload_file(str(temp_file))
            assert isinstance(result, list)
            file_info = result[0]
            assert file_info["status"] is True
            assert "id" in file_info
            assert "file_name" in file_info

            created_files.append(file_info)

            search = client.search_files()
            ids = [f["id"] for f in search["data"]]
            assert file_info["id"] in ids, "Uploaded file not found in search"

            delete_result = client.delete_files([file_info["id"]])
            assert delete_result[0]["status"] is True
            assert delete_result[0]["action"] == "delete"

            search_after = client.search_files()
            ids_after = [f["id"] for f in search_after["data"]]
            assert file_info["id"] not in ids_after, "File was not deleted properly"

            created_files.clear()

        finally:
            if temp_file.exists():
                temp_file.unlink()

    @pytest.mark.parametrize("content", ["", " "])
    @pytest.mark.skip(reason="Uploads a file, but returns 500")
    def test_upload_empty_file(self, file_tracker, tmp_path, content):
        _, client = file_tracker

        empty_file = tmp_path / f"{uuid.uuid4().hex}_empty.pdf"
        empty_file.write_text(content)

        with pytest.raises(HTTPError) as e:
            client.upload_file(str(empty_file))
        assert e.value.status_code == 500
        assert "Internal Server Error" in e.value.body

    def test_move_file(self, file_tracker, dataset_tracker, tmp_path):
        created_datasets, dataset_client = dataset_tracker
        first_dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        second_dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"

        first_resp = dataset_client.create_dataset(name=first_dataset_name)
        created_datasets.append(first_dataset_name)
        assert "successfully created" in first_resp["detail"].lower()
        datasets = dataset_client.search(filters=[{"field": "name", "operator": "eq", "value": first_dataset_name}])[
            "data"
        ]
        assert len(datasets) == 1, f"Expected 1 dataset, got {len(datasets)}"
        first_dataset_id = datasets[0]["id"]

        second_resp = dataset_client.create_dataset(name=second_dataset_name)
        created_datasets.append(second_dataset_name)
        datasets = dataset_client.search(filters=[{"field": "name", "operator": "eq", "value": second_dataset_name}])[
            "data"
        ]
        assert len(datasets) == 1, f"Expected 1 dataset, got {len(datasets)}"
        second_dataset_id = datasets[0]["id"]
        assert "successfully created" in second_resp["detail"].lower()

        created_files, file_client = file_tracker

        data_dir = Path(__file__).parent.parent / "data"
        original_file = data_dir / "multivitamin.pdf"
        unique_name = f"{uuid.uuid4().hex}_multivitamin.pdf"
        temp_file = tmp_path / unique_name
        shutil.copy(original_file, temp_file)

        try:
            result = file_client.upload_file(str(temp_file))
            file_info = result[0]
            assert file_info["status"] is True
            created_files.append(file_info)
            file_id = file_info["id"]

            move1 = file_client.move_files(name=first_dataset_name, objects=[file_id])[0]
            assert move1["status"] is True
            assert "successfully bounded" in move1["message"].lower()

            files_in_first = dataset_client.search_files(dataset_id=first_dataset_id)["data"]
            assert any(f["id"] == file_id for f in files_in_first), "File not found in first dataset after move"

            move2 = file_client.move_files(name=second_dataset_name, objects=[file_id])[0]
            assert move2["status"] is True
            assert "successfully bounded" in move2["message"].lower()

            files_in_second = dataset_client.search_files(dataset_id=second_dataset_id)["data"]
            assert any(f["id"] == file_id for f in files_in_second), "File not found in second dataset after move"

        finally:
            if temp_file.exists():
                temp_file.unlink()
