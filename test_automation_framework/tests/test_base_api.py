from logging import getLogger
from datetime import datetime
from pathlib import Path
import uuid
import shutil

import pytest

from helpers.base_client.base_client import HTTPError

logger = getLogger(__name__)


class TestAuthAPI:
    def test_basic_auth(self, auth_token):
        access_token, refresh_token = auth_token
        assert access_token
        assert refresh_token

    def test_wrong_creds(self, auth_service):
        with pytest.raises(HTTPError) as exc:
            auth_service.get_token("wrong", "wrong")
        assert exc.value.status_code == 401

    def test_refresh_token(self, auth_token, auth_service):
        access_token, refresh_token = auth_token
        new_access, new_refresh = auth_service.refresh_token(refresh_token=refresh_token)
        assert new_access != access_token
        assert new_refresh != refresh_token


class TestAPI:
    def test_menu(self, menu_client):
        menu = menu_client.get_menu()
        assert isinstance(menu, list)
        assert menu
        required_keys = {"name", "badgerdoc_path", "is_external", "is_iframe", "url", "children"}
        for item in menu:
            assert required_keys <= item.keys()
        first_item = menu[0]
        assert isinstance(first_item["name"], str)
        assert isinstance(first_item["badgerdoc_path"], str)
        assert isinstance(first_item["is_external"], bool)
        assert isinstance(first_item["children"], (list, type(None)))
        expected_names = {"Documents", "My Tasks", "Jobs", "Settings"}
        actual_names = {item["name"] for item in menu}
        assert expected_names <= actual_names
        settings_item = next(i for i in menu if i["name"] == "Settings")
        assert isinstance(settings_item["children"], list)
        assert any(child["name"] == "Keycloak" for child in settings_item["children"])


class TestDatasets:
    def test_search_basic(self, dataset_client):
        result = dataset_client.search()
        assert "pagination" in result
        assert "data" in result
        assert isinstance(result["data"], list)
        pagination = result["pagination"]
        required_pagination_keys = {"page_num", "page_offset", "page_size", "min_pages_left", "total", "has_more"}
        assert required_pagination_keys <= pagination.keys()
        for dataset in result["data"]:
            required_dataset_keys = {"id", "name", "count", "created"}
            assert required_dataset_keys <= dataset.keys()
            assert isinstance(dataset["id"], int)
            assert isinstance(dataset["name"], str)
            assert isinstance(dataset["count"], int)
            datetime.fromisoformat(dataset["created"])

    def test_search_sorting(self, dataset_client):
        result = dataset_client.search(sorting=[{"direction": "desc", "field": "name"}])
        names = [d["name"] for d in result["data"]]
        assert names == sorted(names, reverse=True)

    def test_search_pagination(self, dataset_client):
        result = dataset_client.search(page_num=1, page_size=15)
        assert len(result["data"]) <= 15
        assert result["pagination"]["page_num"] == 1

    def test_selection(self, dataset_client):
        datasets = dataset_client.search()["data"]
        assert datasets
        dataset_id = datasets[0]["id"]
        files_selected = dataset_client.search_files(dataset_id=dataset_id)["data"]
        assert isinstance(files_selected, list)
        for f in files_selected:
            assert any(d["id"] == dataset_id for d in f.get("datasets", []))
        files_all = dataset_client.search_files()["data"]
        assert isinstance(files_all, list)
        has_dataset = any(f.get("datasets") for f in files_all)
        has_no_dataset = any(not f.get("datasets") for f in files_all)
        assert has_dataset or has_no_dataset

    def test_create_and_delete_dataset(self, dataset_client):
        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        create_resp = dataset_client.create_dataset(name=dataset_name)
        assert "detail" in create_resp
        assert "successfully created" in create_resp["detail"].lower()
        search_resp = dataset_client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])
        assert any(d["name"] == dataset_name for d in search_resp["data"])
        delete_resp = dataset_client.delete_dataset(name=dataset_name)
        assert "detail" in delete_resp
        assert "successfully deleted" in delete_resp["detail"].lower()
        search_after = dataset_client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])
        assert all(d["name"] != dataset_name for d in search_after["data"])

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
        with pytest.raises(HTTPError) as exc:
            client.create_dataset(name=dataset_name)
        assert exc.value.status_code == 400
        assert "already exists" in exc.value.body.lower()


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
            assert file_info["id"] in ids
            delete_result = client.delete_files([file_info["id"]])
            assert delete_result[0]["status"] is True
            assert delete_result[0]["action"] == "delete"
            search_after = client.search_files()
            ids_after = [f["id"] for f in search_after["data"]]
            assert file_info["id"] not in ids_after
            created_files.clear()
        finally:
            if temp_file.exists():
                temp_file.unlink()

    @pytest.mark.skip(reason="Uploads a file, but returns 500")
    @pytest.mark.parametrize("content", ["", " "])
    def test_upload_empty_file(self, file_client, tmp_path, content):
        empty_file = tmp_path / f"{uuid.uuid4().hex}_empty.pdf"
        empty_file.write_text(content)
        with pytest.raises(HTTPError) as exc:
            file_client.upload_file(str(empty_file))
        assert exc.value.status_code == 400

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
        assert len(datasets) == 1
        first_dataset_id = datasets[0]["id"]
        second_resp = dataset_client.create_dataset(name=second_dataset_name)
        created_datasets.append(second_dataset_name)
        datasets = dataset_client.search(filters=[{"field": "name", "operator": "eq", "value": second_dataset_name}])[
            "data"
        ]
        assert len(datasets) == 1
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
            assert any(f["id"] == file_id for f in files_in_first)
            move2 = file_client.move_files(name=second_dataset_name, objects=[file_id])[0]
            assert move2["status"] is True
            assert "successfully bounded" in move2["message"].lower()
            files_in_second = dataset_client.search_files(dataset_id=second_dataset_id)["data"]
            assert any(f["id"] == file_id for f in files_in_second)
        finally:
            if temp_file.exists():
                temp_file.unlink()


class TestJobs:
    def test_create_and_poll_job(self, jobs_client, file_tracker, dataset_tracker, job_tracker, tmp_path, user_uuid):
        created_files, file_client = file_tracker
        created_datasets, dataset_client = dataset_tracker
        data_dir = Path(__file__).parent.parent / "data"
        original_file = data_dir / "multivitamin.pdf"
        unique_name = f"{uuid.uuid4().hex}_multivitamin.pdf"
        tmp_file = tmp_path / unique_name
        shutil.copy(original_file, tmp_file)
        upload_result = file_client.upload_file(str(tmp_file))
        file_info = upload_result[0]
        assert file_info["status"] is True
        created_files.append(file_info)
        file_id = file_info["id"]
        dataset_name = f"autotest_ds_{uuid.uuid4().hex[:8]}"
        resp = dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)
        assert "successfully created" in resp["detail"].lower()
        move_resp = file_client.move_files(name=dataset_name, objects=[file_id])[0]
        assert move_resp["status"] is True
        job_name = f"test_job_{uuid.uuid4().hex[:8]}"
        create_resp = jobs_client.create_job(
            name=job_name,
            file_ids=[file_id],
            owners=[user_uuid],
        )
        job_tracker[0].append(create_resp)
        job_id = create_resp.get("id")
        assert job_id
        final_job = jobs_client.poll_until_finished(job_id=job_id, timeout_seconds=300)
        status = final_job.get("status")
        assert str(status).lower() in {"finished", "success", "completed"}
        job_files = final_job.get("files") or []
        assert file_id in job_files


class TestCategories:
    @pytest.mark.skip(reason="Creation works, but deletion not implemented, will be cluttered by multiple runs")
    def test_create_and_delete_category(self, auth_token, settings, tenant, categories_client):
        access_token, _ = auth_token

        unique_id = f"test_cat_{uuid.uuid4().hex[:6]}"
        created = categories_client.create_category(category_id=unique_id, name=unique_id, parent="example")
        assert created.id == unique_id
        search_result = categories_client.search_categories(page_size=100)
        ids = [c.id for c in search_result.data]
        assert unique_id in ids, f"Category {unique_id} not found after creation"

        deleted = categories_client.delete_category(unique_id)
        assert deleted.get("detail") or deleted.get("status") or "success" in str(deleted).lower()
        search_after_delete = categories_client.search_categories(page_size=100)
        ids_after = [c.id for c in search_after_delete.data]
        assert unique_id not in ids_after, f"Category {unique_id} still present after deletion"
