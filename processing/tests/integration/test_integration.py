import json
import os
from pathlib import Path
from time import sleep

import pytest
import requests
from dotenv import load_dotenv
from minio import Minio, S3Error
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

pytestmark = pytest.mark.integration

load_dotenv("./.env")

S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
EXPORT_BUCKET = os.getenv("EXPORT_BUCKET")
MODEL_NAME = os.getenv("MODEL_NAME")

BUCKET = "test"

INTEGRATION_DIR = Path(__file__).parent.absolute()
JSON1 = str(INTEGRATION_DIR / "test_files/1.json")
JSON2 = str(INTEGRATION_DIR / "test_files/2.json")
JSONS = [JSON1, JSON2]
PDF = str(INTEGRATION_DIR / "test_files/52.pdf")


@pytest.fixture(scope="module")
def minio_url(module_scoped_container_getter):
    """Wait for the api from minio to become responsive"""
    request_session = requests.Session()
    retries = Retry(total=5, backoff_factor=1)
    request_session.mount("http://", HTTPAdapter(max_retries=retries))
    service = module_scoped_container_getter.get("minio").network_info[0]
    api_url = f"{service.hostname}:{service.host_port}"
    return api_url


@pytest.fixture(scope="module")
def processing_url(module_scoped_container_getter):
    """Wait for the api from processing to become responsive"""
    request_session = requests.Session()
    retries = Retry(total=5, backoff_factor=1)
    request_session.mount("http://", HTTPAdapter(max_retries=retries))
    service = module_scoped_container_getter.get("processing").network_info[0]
    api_url = f"http://{service.hostname}:{service.host_port}"
    return api_url


@pytest.fixture(scope="module")
def preprocessing_url(module_scoped_container_getter):
    """Wait for the api from processing to become responsive"""
    request_session = requests.Session()
    retries = Retry(total=5, backoff_factor=1)
    request_session.mount("http://", HTTPAdapter(max_retries=retries))
    service = module_scoped_container_getter.get("preprocessing").network_info[
        0
    ]
    api_url = f"http://{service.hostname}:{service.host_port}"
    return api_url


@pytest.fixture(scope="module")
def minio_client(minio_url):
    return Minio(
        minio_url,
        access_key=S3_ACCESS_KEY,
        secret_key=S3_SECRET_KEY,
        secure=False,
    )


@pytest.fixture(scope="module")
def file_id(minio_client):
    file_id = "52"
    minio_path = f"files/{file_id}/"
    try:
        minio_client.make_bucket(BUCKET)
    except S3Error:  # bucket already exist
        pass
    for i in range(2):
        minio_client.fput_object(
            BUCKET,
            os.path.join(minio_path, f"ocr/{i + 1}.json"),
            JSONS[i],
        )

    minio_client.fput_object(
        BUCKET,
        os.path.join(minio_path, "52.pdf"),
        PDF,
    )
    return file_id


@pytest.mark.skip(
    "Fails with ValueError: Unable to find `/processing/docker-compose.yml` "
    "for integration tests."
)
def test_minio_ok(minio_url, minio_client, file_id):
    objs = minio_client.list_objects(
        BUCKET, f"files/{file_id}", recursive=True
    )
    file_names = [i.object_name for i in objs]
    assert set(file_names) == {
        "files/52/52.pdf",
        "files/52/ocr/1.json",
        "files/52/ocr/2.json",
    }


@pytest.mark.skip(
    "Fails with ValueError: Unable to find `/processing/docker-compose.yml` "
    "for integration tests."
)
def test_url(minio_url, processing_url, preprocessing_url):
    assert "0.0.0.0:9000" in str(minio_url)
    assert "0.0.0.0:8080" in str(processing_url)
    assert "0.0.0.0:65432" in str(preprocessing_url)


@pytest.mark.skip(
    "Fails with ValueError: Unable to find `/processing/docker-compose.yml` "
    "for integration tests."
)
def test_get_preprocessing_results_all_pages(processing_url, file_id):
    response = requests.get(
        url=processing_url.rstrip("/") + f"/tokens/{file_id}",
        headers={"X-Current-Tenant": "test"},
    )
    with open(JSON1) as file1, open(JSON2) as file2:
        assert response.json() == [json.load(file1), json.load(file2)]


@pytest.mark.skip(
    "Fails with ValueError: Unable to find `/processing/docker-compose.yml` "
    "for integration tests."
)
def test_get_preprocessing_results_some_pages(processing_url, file_id):
    response = requests.get(
        url=processing_url.rstrip("/") + f"/tokens/{file_id}",
        headers={"X-Current-Tenant": "test"},
        params={"pages": [2]},
    )
    with open(JSON2) as file2:
        file2_json = json.load(file2)
    assert len(response.json()) == 1
    assert response.json() == [file2_json]


@pytest.mark.skip(
    "Fails with ValueError: Unable to find `/processing/docker-compose.yml` "
    "for integration tests."
)
def test_send_request_to_preprocessing(
    preprocessing_url, processing_url, minio_client, monkeypatch
):
    minio_client.fput_object(BUCKET, "files/1/1.pdf", PDF)
    response = requests.post(
        url=processing_url.rstrip("/") + "/run_preprocess",
        headers={"X-Current-Tenant": "test"},
        json={"model_id": "preprocessing", "file_id": "1", "pages": [1, 2]},
    )

    assert response.status_code == 202
    sleep(1)
    objs = set(
        minio_client.list_objects(BUCKET, "files/1/ocr", recursive=True)
    )
    assert set((i.object_name for i in objs)) == {
        "files/1/ocr/2.json",
        "files/1/ocr/1.json",
    }
