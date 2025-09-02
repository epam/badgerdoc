from logging import getLogger
from datetime import datetime, timedelta
import uuid

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
    def test_clear_search_for_datasets(self, dataset_client):
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

    def test_search_existing_dataset(self, dataset_tracker):
        created, client = dataset_tracker
        dataset_name = f"autotest_{uuid.uuid4().hex[:8]}"
        resp = client.create_dataset(name=dataset_name)
        created.append(dataset_name)
        assert "successfully created" in resp["detail"].lower()

        search_resp = client.search(filters=[{"field": "name", "operator": "eq", "value": dataset_name}])
        names = [d["name"] for d in search_resp["data"]]
        assert dataset_name in names

    def test_search_non_existing_dataset(self, dataset_client):
        search_resp = dataset_client.search(
            filters=[{"field": "name", "operator": "eq", "value": "non_existing_dataset"}]
        )
        assert search_resp["data"] == []

    def test_search_multiple_existing_datasets(self, dataset_tracker):
        created, client = dataset_tracker
        names = [f"autotest_{uuid.uuid4().hex[:8]}" for _ in range(2)]
        for n in names:
            resp = client.create_dataset(name=n)
            created.append(n)
            assert "successfully created" in resp["detail"].lower()

        search_resp = client.search(filters=[{"field": "name", "operator": "in", "value": names}])
        found_names = {d["name"] for d in search_resp["data"]}
        assert set(names) <= found_names


class TestFiles:
    def test_upload_and_delete_file(self, file_tracker, tmp_path):
        created_files, client = file_tracker
        try:
            file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
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
        first_dataset_id = dataset_client.search(
            filters=[{"field": "name", "operator": "eq", "value": first_dataset_name}]
        )["data"][0]["id"]

        second_resp = dataset_client.create_dataset(name=second_dataset_name)
        created_datasets.append(second_dataset_name)
        assert "successfully created" in second_resp["detail"].lower()
        second_dataset_id = dataset_client.search(
            filters=[{"field": "name", "operator": "eq", "value": second_dataset_name}]
        )["data"][0]["id"]

        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        created_files.append(file_info)
        file_id = file_info["id"]
        try:
            move1 = client.move_files(name=first_dataset_name, objects=[file_id])[0]
            assert move1["status"] is True
            assert "successfully bounded" in move1["message"].lower()
            files_in_first = dataset_client.search_files(dataset_id=first_dataset_id)["data"]
            assert any(f["id"] == file_id for f in files_in_first)
            move2 = client.move_files(name=second_dataset_name, objects=[file_id])[0]
            assert move2["status"] is True
            assert "successfully bounded" in move2["message"].lower()
            files_in_second = dataset_client.search_files(dataset_id=second_dataset_id)["data"]
            assert any(f["id"] == file_id for f in files_in_second)
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_search_existing_file(self, file_tracker, tmp_path):
        created_files, client = file_tracker
        try:
            file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
            assert file_info["status"] is True
            search_resp = client.search_files(
                filters=[{"field": "original_name", "operator": "eq", "value": file_info["file_name"]}]
            )
            names = [f["original_name"] for f in search_resp["data"]]
            assert file_info["file_name"] in names
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_search_non_existing_file(self, file_client):
        search_resp = file_client.search_files(
            filters=[{"field": "original_name", "operator": "eq", "value": "definitely_not_a_file.pdf"}]
        )
        assert search_resp["data"] == []

    def test_search_multiple_existing_files(self, file_tracker, tmp_path):
        created_files, client = file_tracker
        f1, t1 = client.upload_temp_file(client, file_tracker, tmp_path)
        f2, t2 = client.upload_temp_file(client, file_tracker, tmp_path)
        names = [f1["file_name"], f2["file_name"]]

        search = client.search_files(filters=[{"field": "original_name", "operator": "in", "value": names}])
        found_names = {f["original_name"] for f in search["data"]}
        assert set(names) <= found_names

        t1.unlink(missing_ok=True)
        t2.unlink(missing_ok=True)

    def test_download_existing_file(self, file_tracker, tmp_path):
        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        file_id = file_info["id"]

        content = client.download_file(file_id)
        assert isinstance(content, (bytes, bytearray))
        assert len(content) > 100
        assert content.startswith(b"%PDF")

        temp_file.unlink(missing_ok=True)

    def test_download_nonexistent_file(self, file_client):
        with pytest.raises(HTTPError) as exc:
            file_client.download_file(9999999)
        assert exc.value.status_code == 404


class TestJobs:
    def test_create_and_poll_job(
        self, file_client, jobs_client, file_tracker, dataset_tracker, job_tracker, tmp_path, user_uuid
    ):
        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_ds_{uuid.uuid4().hex[:8]}"
        dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)
        move_resp = file_client.move_files(name=dataset_name, objects=[file_info["id"]])[0]
        assert move_resp["status"] is True
        job_name = f"test_job_{uuid.uuid4().hex[:8]}"
        create_resp = jobs_client.create_job(
            name=job_name,
            file_ids=[file_info["id"]],
            owners=[user_uuid],
        )
        job_tracker[0].append(create_resp)
        job_id = create_resp.get("id")
        assert job_id
        final_job = jobs_client.poll_until_finished(job_id=job_id, timeout_seconds=300)
        status = final_job.get("status")
        assert str(status).lower() in {"finished", "success", "completed"}
        job_files = final_job.get("files") or []
        assert file_info["id"] in job_files

    @pytest.mark.parametrize("field", ["name", "type", "status", "deadline", "creation_datetime"])
    @pytest.mark.parametrize("direction", ["asc", "desc"])
    # descending name sorting works weird
    def test_sorting(self, jobs_client, field, direction):
        resp = jobs_client.post_json(
            "/jobs/jobs/search",
            json={
                "pagination": {"page_num": 1, "page_size": 15},
                "filters": [],
                "sorting": [{"direction": direction, "field": field}],
            },
            headers=jobs_client._default_headers(content_type_json=True),
        )
        data = resp["data"]
        values = [d[field] for d in data if field in d and d[field] is not None]

        if field in {"creation_datetime", "deadline"}:
            values = [datetime.fromisoformat(v) for v in values]

        expected = sorted(values, reverse=(direction == "desc"))
        assert values == expected

    @pytest.mark.parametrize("field", ["name", "type", "status", "deadline", "creation_datetime"])
    def test_job_search(self, jobs_client, job_tracker, file_tracker, dataset_tracker, user_uuid, tmp_path, field):
        created_files, client = file_tracker
        file_info, temp_file = client.upload_temp_file(client, file_tracker, tmp_path)
        created_datasets, dataset_client = dataset_tracker

        dataset_name = f"autotest_ds_{uuid.uuid4().hex[:8]}"
        dataset_client.create_dataset(name=dataset_name)
        created_datasets.append(dataset_name)

        job_name = f"test_job_{uuid.uuid4().hex[:8]}"
        create_resp = jobs_client.create_job(
            name=job_name,
            file_ids=[file_info["id"]],
            owners=[user_uuid],
        )
        job_id = create_resp.get("id")
        jobs_client.poll_until_finished(job_id=job_id, timeout_seconds=300)
        job_tracker[0].append(create_resp)
        search_value = create_resp.get(field, None)

        filters = [
            {"field": field, "operator": "eq", "value": search_value},
            {"field": "name", "operator": "eq", "value": job_name},
        ]

        search_resp = jobs_client.post_json(
            "/jobs/jobs/search",
            json={
                "pagination": {"page_num": 1, "page_size": 100},
                "filters": filters,
            },
            headers=jobs_client._default_headers(content_type_json=True),
        )

        job_ids = [j["id"] for j in search_resp["data"]]
        assert job_id in job_ids

    @pytest.mark.parametrize("field", ["creation_datetime", "deadline"])
    def test_date_range_filter(self, jobs_client, field):
        start = (datetime.utcnow() - timedelta(days=365)).replace(microsecond=0).isoformat()
        end = (datetime.utcnow() + timedelta(days=365)).replace(microsecond=0).isoformat()

        resp = jobs_client.post_json(
            "/jobs/jobs/search",
            json={
                "pagination": {"page_num": 1, "page_size": 15},
                "filters": [
                    {"field": field, "operator": "ge", "value": start},
                    {"field": field, "operator": "le", "value": end},
                ],
            },
            headers=jobs_client._default_headers(content_type_json=True),
        )

        data = resp["data"]
        for job in data:
            if field in job and job[field] is not None:
                date_val = datetime.fromisoformat(job[field])
                assert datetime.fromisoformat(start) <= date_val <= datetime.fromisoformat(end)


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


class TestReports:
    def test_export_tasks_csv(self, reports_client, user_uuid):
        csv_text = reports_client.export_tasks(
            user_ids=[user_uuid],
            date_from="2025-05-01 00:00:00",
            date_to="2025-08-31 00:00:00",
        )
        assert "annotator_id" in csv_text
        assert "task_id" in csv_text

    @pytest.mark.parametrize(
        "date_from,date_to",
        [
            ("2028-05-01 00:00:00", "2028-08-31 00:00:00"),
            ("1900-01-01 00:00:00", "1900-12-31 00:00:00"),
            ("2025-09-01 00:00:00", "2025-08-01 00:00:00"),
        ],
    )
    def test_export_tasks_wrong_date(self, reports_client, user_uuid, date_from, date_to):
        with pytest.raises(HTTPError) as exc:
            reports_client.export_tasks(
                user_ids=[user_uuid],
                date_from=date_from,
                date_to=date_to,
            )
        assert exc.value.status_code == 406


class TestPlugins:
    def test_create_and_delete_plugin(self, plugins_tracker):
        created, plugins_client = plugins_tracker
        unique_name = f"plugin_{uuid.uuid4().hex[:8]}"
        resp = plugins_client.create_plugin(
            name=unique_name,
            menu_name=unique_name,
            description="bar",
            version="1",
            url="http://what.com/what",
            is_iframe=True,
        )
        plugin_id = resp["id"]
        created.append(plugin_id)

        plugins = plugins_client.get_plugins()
        assert any(p["id"] == plugin_id for p in plugins)
        assert any(p["name"] == unique_name for p in plugins)

        plugins_client.delete_plugin(plugin_id)

        plugins = plugins_client.get_plugins()
        assert not any(p["id"] == plugin_id for p in plugins)

    def test_update_plugin(self, plugins_tracker):
        created, plugins_client = plugins_tracker
        unique_name = f"plugin_{uuid.uuid4().hex[:8]}"
        resp = plugins_client.create_plugin(
            name=unique_name,
            menu_name=unique_name,
            description="bar",
            version="1",
            url="http://what.com/what",
            is_iframe=True,
        )
        plugin_id = resp["id"]
        created.append(plugin_id)

        updated_payload = {
            "name": unique_name,
            "menu_name": unique_name,
            "description": "updated desc",
            "version": "1",
            "url": "http://what.com/what",
            "is_iframe": True,
        }
        update_resp = plugins_client.update_plugin(plugin_id, **updated_payload)
        assert update_resp["description"] == "updated desc"

        plugins = plugins_client.get_plugins()
        updated = next(p for p in plugins if p["id"] == plugin_id)
        assert updated["description"] == "updated desc"
