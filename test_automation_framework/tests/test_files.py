from logging import getLogger
from datetime import datetime
import uuid

import pytest


from helpers.base_client.base_client import HTTPError

logger = getLogger(__name__)


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

    def test_upload_invalid_format(self, file_client, tmp_path):
        invalid_file = tmp_path / f"{uuid.uuid4().hex}.py"
        invalid_file.write_text("this is py file")

        with pytest.raises(HTTPError) as exc:
            file_client.upload_file(str(invalid_file))

        assert exc.value.status_code == 400

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

    def test_clear_search_files(self, file_tracker, tmp_path):
        created_files, client = file_tracker
        result = client.search_files()
        assert "pagination" in result
        assert "data" in result
        assert isinstance(result["data"], list)
        pagination = result["pagination"]
        required_pagination_keys = {"page_num", "page_offset", "page_size", "min_pages_left", "total", "has_more"}
        assert required_pagination_keys <= pagination.keys()
        for file in result["data"]:
            required_file_keys = {
                "id",
                "original_name",
                "bucket",
                "size_in_bytes",
                "extension",
                "original_ext",
                "content_type",
                "pages",
                "last_modified",
                "status",
                "path",
                "datasets",
            }
            assert required_file_keys <= file.keys()
            assert isinstance(file["id"], int)
            assert isinstance(file["original_name"], str)
            assert isinstance(file["size_in_bytes"], int)

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

    @pytest.mark.parametrize("field", ["original_name", "last_modified", "size_in_bytes"])
    @pytest.mark.parametrize("direction", ["asc", "desc"])
    # name descending fails
    def test_files_sorting(self, file_client, field, direction):
        resp = file_client.post_json(
            "/assets/files/search",
            json={
                "pagination": {"page_num": 1, "page_size": 15},
                "filters": [{"field": "original_name", "operator": "ilike", "value": "%%"}],
                "sorting": [{"direction": direction, "field": field}],
            },
            headers=file_client._default_headers(content_type_json=True),
        )

        data = resp["data"]
        values = [d[field] for d in data if field in d]

        if field == "last_modified":
            values = [datetime.fromisoformat(v) for v in values]

        if field == "size_in_bytes":
            values = [int(v) for v in values]

        expected = sorted(values, reverse=(direction == "desc"))
        assert values == expected, f"{field} not sorted {direction}"
