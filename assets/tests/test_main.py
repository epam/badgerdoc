# flake8: noqa: F501
import json
import uuid
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from requests import Response

from .conftest import BUCKET_TESTS


def test_create_bucket(client_app_main_bucket_false):
    random_name = "tests" + uuid.uuid4().hex
    bucket = {"name": random_name}
    tests_bucket = client_app_main_bucket_false.post(
        "/bucket", data=json.dumps(bucket)
    )
    assert tests_bucket.status_code == 201


def test_bucket_name_on_create_bucket_with_prefix(client_app_main_bucket_false, monkeypatch):
    test_prefix = 'test_prefix'

    from src.config import settings
    monkeypatch.setattr(target=settings, name='s3_prefix', value=test_prefix)

    random_name = "tests" + uuid.uuid4().hex
    bucket = {"name": random_name}
    response = client_app_main_bucket_false.post("/bucket", data=json.dumps(bucket))
    assert response.status_code == 201
    assert (
        response.json()["detail"]
        == f"Bucket {test_prefix}-{random_name} successfully created!"
    )


def test_bucket_name_on_create_bucket_without_prefix(client_app_main_bucket_false, monkeypatch):
    test_prefix = None

    from src.config import settings
    monkeypatch.setattr(target=settings, name='s3_prefix', value=test_prefix)

    random_name = "tests" + uuid.uuid4().hex
    bucket = {"name": random_name}
    response = client_app_main_bucket_false.post("/bucket", data=json.dumps(bucket))
    assert response.status_code == 201
    assert response.json()["detail"] == f"Bucket {random_name} successfully created!"


def test_upload_and_delete_file_without_conversion(client_app_main):
    with NamedTemporaryFile(suffix=".py") as file:
        data = {"files": file}
        response = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )
    assert response.status_code == 201

    id_ = response.json()[0]["id"]
    body = {"bucket_name": BUCKET_TESTS, "objects": [id_]}
    res = client_app_main.delete("/files", data=json.dumps(body))
    assert res.status_code == 201
    assert id_ == res.json()[0]["id"]


@patch("src.utils.s3_utils.S3Manager.get_files")
@patch("src.utils.s3_utils.S3Manager.check_s3")
def test_upload_and_delete_file_s3(
    check_s3, get_files, client_app_main, s3_retrieved_file
):
    check_s3.return_value = None
    get_files.return_value = s3_retrieved_file

    body = {
        "access_key_id": "a",
        "secret_access_key": "b",
        "bucket_s3": "some_bucket",
        "files_keys": ["some_file1.pdf"],
    }
    q = {"storage_url": None}

    response = client_app_main.post(
        "/s3_upload",
        headers={"X-Current-Tenant": BUCKET_TESTS},
        data=json.dumps(body),
        params=q,
    )

    assert response.status_code == 201

    id_ = response.json()[0]["id"]
    body = {"bucket_name": BUCKET_TESTS, "objects": [id_]}
    res = client_app_main.delete("/files", data=json.dumps(body))
    assert res.status_code == 201
    assert id_ == res.json()[0]["id"]


def test_upload_negative(client_app_main):
    with NamedTemporaryFile() as file:
        data = {"files": file}
        response = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )
    assert not response.json()[0]["status"]
    assert response.status_code == 201


def test_get_files(client_app_main):
    with NamedTemporaryFile(suffix=".pdf") as file:
        data = {"files": file}
        response = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )
    file_id = response.json()[0]["id"]

    res_get = client_app_main.post("/files/search", data="{}")
    keys = [x["id"] for x in res_get.json()["data"]]
    assert file_id in keys
    assert res_get.status_code == 200

    body = {"bucket_name": BUCKET_TESTS, "objects": [file_id]}

    res_delete = client_app_main.delete("/files", data=json.dumps(body))
    assert res_delete.status_code == 201
    assert file_id == res_delete.json()[0]["id"]


def test_get_file_by_id(client_app_main):
    with NamedTemporaryFile(suffix=".go") as file:
        data = {"files": file}
        response = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )
    file_id = response.json()[0]["id"]

    search_body = {
        "filters": [{"field": "id", "operator": "eq", "value": file_id}]
    }
    res_get_one = client_app_main.post(
        "/files/search", data=json.dumps(search_body)
    )
    assert res_get_one.status_code == 200
    assert res_get_one.json()["data"][0]["id"] == file_id

    delete_body = {"bucket_name": BUCKET_TESTS, "objects": [file_id]}
    res_delete = client_app_main.delete("/files", data=json.dumps(delete_body))
    assert res_delete.status_code == 201
    assert file_id == res_delete.json()[0]["id"]


def test_get_files_by_dataset_negative(client_app_main):
    dataset = "1231231312313123123213131"
    res = client_app_main.post(f"/datasets/{dataset}/files/search", data="{}")
    assert res.status_code == 404
    assert res.json() == {"detail": f"Dataset {dataset} does not exist!"}


def test_get_datasets(client_app_main):
    res = client_app_main.post("/datasets/search", data="{}")
    assert res.status_code == 200
    assert res.json() == {
        "pagination": {
            "has_more": False,
            "min_pages_left": 0,
            "page_num": 1,
            "page_size": 15,
            "total": 0,
        },
        "data": [],
    }


def test_put_and_delete_dataset(client_app_main):
    random_name = uuid.uuid4().hex
    body = {"name": random_name}
    res = client_app_main.post("/datasets", data=json.dumps(body))
    assert res.status_code == 201
    assert res.json() == {
        "detail": f"Dataset {random_name} successfully created!"
    }

    res_delete = client_app_main.delete("/datasets", data=json.dumps(body))
    assert res_delete.status_code == 201
    assert res_delete.json() == {
        "detail": f"Dataset {random_name} successfully deleted!"
    }


def test_bound_and_unbound(client_app_main):
    with NamedTemporaryFile(suffix=".py") as file:
        data = {"files": file}
        res_upload = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )

    file_id = res_upload.json()[0]["id"]
    assert res_upload.status_code == 201

    dataset_name = uuid.uuid4().hex
    body = {"name": dataset_name}
    res_put = client_app_main.post("/datasets", data=json.dumps(body))
    assert res_put.status_code == 201

    data = {"name": dataset_name, "objects": [file_id]}
    res_bound = client_app_main.post("/datasets/bonds", data=json.dumps(data))
    assert res_bound.status_code == 201
    assert file_id == res_bound.json()[0]["id"]
    assert res_bound.json()[0]["status"]

    count_body = {
        "filters": [{"field": "name", "operator": "eq", "value": dataset_name}]
    }
    res_count = client_app_main.post(
        "/datasets/search", data=json.dumps(count_body)
    )
    assert res_count.json()["data"][0]["count"] == 1

    res_unbound = client_app_main.delete(
        "/datasets/bonds", data=json.dumps(data)
    )
    assert res_unbound.status_code == 201
    assert file_id == res_unbound.json()[0]["id"]
    assert res_unbound.json()[0]["status"]

    res_delete_dataset = client_app_main.delete(
        "/datasets", data=json.dumps(body)
    )
    assert res_delete_dataset.status_code == 201
    assert res_delete_dataset.json() == {
        "detail": f"Dataset {dataset_name} successfully deleted!"
    }

    file_body = {"bucket_name": BUCKET_TESTS, "objects": [file_id]}
    res_delete_file = client_app_main.delete(
        f"/files?bucket={BUCKET_TESTS}", data=json.dumps(file_body)
    )
    assert res_delete_file.status_code == 201
    assert file_id == res_delete_file.json()[0]["id"]
    assert res_delete_file.json()[0]["status"]


def test_get_files_by_dataset(client_app_main):
    with NamedTemporaryFile(suffix=".env") as file:
        data = {"files": file}
        res_upload = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )
    file_id = res_upload.json()[0]["id"]
    assert res_upload.status_code == 201
    assert res_upload.json()[0]["status"]

    dataset_name = uuid.uuid4().hex
    body = {"name": dataset_name}
    res_put = client_app_main.post("/datasets", data=json.dumps(body))
    assert res_put.status_code == 201

    bound_data = {"name": dataset_name, "objects": [file_id]}
    res_bound = client_app_main.post(
        "/datasets/bonds", data=json.dumps(bound_data)
    )
    assert res_bound.status_code == 201
    assert file_id == res_bound.json()[0]["id"]
    assert res_bound.json()[0]["status"]

    res_get_by_dataset = client_app_main.post(
        f"/datasets/{dataset_name}/files/search", data="{}"
    )
    assert res_get_by_dataset.status_code == 200
    assert res_get_by_dataset.json()["data"][0]["id"] == file_id

    res_delete_dataset = client_app_main.delete(
        "/datasets", data=json.dumps(body)
    )
    assert res_delete_dataset.status_code == 201
    assert res_delete_dataset.json() == {
        "detail": f"Dataset {dataset_name} successfully deleted!"
    }

    file_body = {"bucket_name": BUCKET_TESTS, "objects": [file_id]}
    res_delete_file = client_app_main.delete(
        "/files", data=json.dumps(file_body)
    )
    assert res_delete_file.status_code == 201
    assert file_id == res_delete_file.json()[0]["id"]
    assert res_delete_file.json()[0]["status"]


def test_get_bonds(client_app_main):
    with NamedTemporaryFile(suffix=".pdf") as file:
        data = {"files": file}
        res_upload = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )
    file_id = res_upload.json()[0]["id"]
    assert res_upload.status_code == 201
    assert res_upload.json()[0]["status"]

    dataset_name = uuid.uuid4().hex
    body = {"name": dataset_name}
    res_put = client_app_main.post("/datasets", data=json.dumps(body))
    assert res_put.status_code == 201

    data = {"name": dataset_name, "objects": [file_id]}
    res_bound = client_app_main.post("/datasets/bonds", data=json.dumps(data))
    assert res_bound.status_code == 201
    assert file_id == res_bound.json()[0]["id"]
    assert res_bound.json()[0]["status"]

    res_get_bonds = client_app_main.post("/datasets/bonds/search", data="{}")
    assert res_get_bonds.status_code == 200
    assert res_get_bonds.json()["data"] == [
        {"dataset_name": dataset_name, "file_id": file_id}
    ]

    file_body = {"bucket_name": BUCKET_TESTS, "objects": [file_id]}
    res_delete_file = client_app_main.delete(
        f"/files?bucket={BUCKET_TESTS}", data=json.dumps(file_body)
    )
    assert res_delete_file.status_code == 201
    assert file_id == res_delete_file.json()[0]["id"]
    assert res_delete_file.json()[0]["status"]


def test_get_dataset_by_name(client_app_main):
    random_name = uuid.uuid4().hex
    body = {"name": random_name}
    res = client_app_main.post("/datasets", data=json.dumps(body))
    assert res.status_code == 201
    assert res.json() == {
        "detail": f"Dataset {random_name} successfully created!"
    }

    search_body = {
        "filters": [{"field": "name", "operator": "eq", "value": random_name}]
    }
    res_id = client_app_main.post(
        "/datasets/search", data=json.dumps(search_body)
    )
    assert res_id.status_code == 200
    assert res_id.json()["data"][0]["id"] == 1
    assert res_id.json()["data"][0]["name"] == random_name
    assert res_id.json()["data"][0]["count"] == 0

    res_delete = client_app_main.delete("/datasets", data=json.dumps(body))
    assert res_delete.status_code == 201
    assert res_delete.json() == {
        "detail": f"Dataset {random_name} successfully deleted!"
    }


def test_get_files_by_filename_positive(client_app_main):
    with NamedTemporaryFile(suffix=".js") as file:
        data = {"files": file}
        res_upload_1 = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )
        res_upload_2 = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )
        res_upload_3 = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )

    assert res_upload_1.status_code == 201
    id_1 = res_upload_1.json()[0]["id"]

    assert res_upload_2.status_code == 201
    id_2 = res_upload_2.json()[0]["id"]

    assert res_upload_3.status_code == 201
    id_3 = res_upload_3.json()[0]["id"]

    assert (
        res_upload_1.json()[0]["file_name"]
        == res_upload_2.json()[0]["file_name"]
        == res_upload_3.json()[0]["file_name"]
    )

    file_name = res_upload_1.json()[0]["file_name"]
    search_body = {
        "filters": [
            {"field": "original_name", "operator": "eq", "value": file_name}
        ]
    }
    get_by_name = client_app_main.post(
        "/files/search", data=json.dumps(search_body)
    )
    assert get_by_name.status_code == 200

    all_names = [el["original_name"] for el in get_by_name.json()["data"]]
    assert len(get_by_name.json()["data"]) == 3
    assert all_names == [file_name, file_name, file_name]

    file_body = {"bucket_name": BUCKET_TESTS, "objects": [id_1, id_2, id_3]}
    res_delete = client_app_main.delete("/files", data=json.dumps(file_body))
    assert res_delete.status_code == 201


def test_get_files_by_filename_empty_array(client_app_main):
    with NamedTemporaryFile(suffix=".jpg") as file:
        data = {"files": file}
        res_upload = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )
    id_ = res_upload.json()[0]["id"]
    assert res_upload.status_code == 201
    assert res_upload.json()[0]["status"]

    search_body = {
        "filters": [{"field": "id", "operator": "eq", "value": id_ + 10111}]
    }
    get_by_name = client_app_main.post(
        "/files/search", data=json.dumps(search_body)
    )
    assert get_by_name.status_code == 200
    assert get_by_name.json()["data"] == []

    file_body = {"bucket_name": BUCKET_TESTS, "objects": [id_]}
    res_delete = client_app_main.delete("/files", data=json.dumps(file_body))
    assert res_delete.status_code == 201


def test_download_negative(client_app_main):
    some_id = 1231212312
    res = client_app_main.get(f"/download?file_id={some_id}")
    assert res.status_code == 404


def test_download_positive(client_app_main):
    with patch("src.routers.minio_router.fastapi.responses.StreamingResponse"):
        with NamedTemporaryFile(suffix=".jpg") as file:
            data = {"files": file}
            res_upload = client_app_main.post(
                "/files",
                files=data,
                headers={"X-Current-Tenant": BUCKET_TESTS},
            )
        id_ = res_upload.json()[0]["id"]
        assert res_upload.status_code == 201
        assert res_upload.json()[0]["status"]

        res_download = client_app_main.get(f"/download?file_id={id_}")
        assert res_download.status_code == 200


@patch("src.utils.common_utils.requests.post")
def test_download_positive_originals(
    gotenberg, pdf_file_bytes, client_app_main
):
    response = Response()
    response._content = pdf_file_bytes
    gotenberg.return_value = response
    with patch("src.routers.minio_router.fastapi.responses.StreamingResponse"):
        with NamedTemporaryFile(suffix=".doc", prefix="some_file") as file:
            data = {"files": file}
            res_upload = client_app_main.post(
                "/files",
                files=data,
                headers={"X-Current-Tenant": BUCKET_TESTS},
            )
        id_ = res_upload.json()[0]["id"]
        assert res_upload.status_code == 201
        assert res_upload.json()[0]["status"]

        res_download = client_app_main.get(
            f"/download?file_id={id_}&original=true"
        )
        assert res_download.status_code == 200


def test_count_changing(client_app_main):
    with NamedTemporaryFile(suffix=".py") as file:
        data = {"files": file}
        res_upload = client_app_main.post(
            "/files", files=data, headers={"X-Current-Tenant": BUCKET_TESTS}
        )

    file_id = res_upload.json()[0]["id"]
    assert res_upload.status_code == 201

    dataset_name = uuid.uuid4().hex
    body = {"name": dataset_name}
    res_put = client_app_main.post("/datasets", data=json.dumps(body))
    assert res_put.status_code == 201

    data = {"name": dataset_name, "objects": [file_id]}
    res_bound = client_app_main.post("/datasets/bonds", data=json.dumps(data))
    assert res_bound.status_code == 201
    assert file_id == res_bound.json()[0]["id"]
    assert res_bound.json()[0]["status"]

    count_body = {
        "filters": [{"field": "name", "operator": "eq", "value": dataset_name}]
    }
    res_count = client_app_main.post(
        "/datasets/search", data=json.dumps(count_body)
    )
    assert res_count.json()["data"][0]["count"] == 1

    id_ = res_upload.json()[0]["id"]
    body_delete = {"bucket_name": BUCKET_TESTS, "objects": [id_]}
    res_delete = client_app_main.delete("/files", data=json.dumps(body_delete))
    assert res_delete.status_code == 201
    assert file_id == res_delete.json()[0]["id"]
    assert res_delete.json()[0]["status"]

    res_changed_count = client_app_main.post(
        "/datasets/search", data=json.dumps(count_body)
    )
    assert res_changed_count.json()["data"][0]["count"] == 0
