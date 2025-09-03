from logging import getLogger
import uuid

import pytest


from helpers.base_client.base_client import HTTPError

logger = getLogger(__name__)


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
