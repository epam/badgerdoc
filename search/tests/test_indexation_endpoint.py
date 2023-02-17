from unittest.mock import Mock, patch

from botocore.exceptions import BotoCoreError
from elasticsearch.exceptions import ElasticsearchException
from fastapi.testclient import TestClient
from pytest import mark

from search.config import settings
from search.es import NoSuchTenant
from search.main import app

from .override_app_dependency import TEST_HEADERS, TEST_TOKEN

client = TestClient(app)
HEADER_TENANT = "X-Current-Tenant"


@mark.integration
@mark.parametrize("job_id", (1, 2, 100))
def test_successful_response(monkeypatch, drop_es_index, job_id, es):
    monkeypatch.setattr(
        "search.harvester.connect_s3", Mock(return_value=drop_es_index)
    )
    monkeypatch.setattr("search.harvester.ES", es)
    response = client.post(
        f"{settings.indexation_path}/{job_id}",
        headers=TEST_HEADERS,
    )
    assert response.status_code == 204
    assert not response.text


@mark.integration
@mark.parametrize(
    ["tenant", "drop_parametrized_index"],
    [
        ("wrong_tenant_1", "wrong_tenant_1"),
        ("wrong_tenant_2", "wrong_tenant_2"),
    ],
    indirect=["drop_parametrized_index"],
)
def test_no_such_tenant_bucket(drop_parametrized_index, tenant):
    with patch(
        "search.harvester.connect_s3",
        side_effect=NoSuchTenant(f"Bucket for tenant {tenant} doesn't exist"),
    ):
        headers = {
            HEADER_TENANT: tenant,
            "Authorization": f"Bearer: {TEST_TOKEN}",
        }
        response = client.post(
            f"{settings.indexation_path}/1",
            headers=headers,
        )
        assert response.status_code == 404
        assert f"Bucket for tenant {tenant} doesn't exist" in response.text


@mark.integration
def test_minio_connection_error(monkeypatch, moto_s3):
    monkeypatch.setattr(
        "search.harvester.connect_s3", Mock(side_effect=BotoCoreError)
    )
    response = client.post(
        f"{settings.indexation_path}/1",
        headers=TEST_HEADERS,
    )
    assert response.status_code == 500
    assert "Error: connection error" in response.text


@mark.integration
def test_elasticsearch_connection_error(monkeypatch, moto_s3):
    monkeypatch.setattr(
        "search.harvester.connect_s3", Mock(return_value=moto_s3)
    )
    monkeypatch.setattr(
        "search.harvester.old_pieces_cleaner",
        Mock(side_effect=ElasticsearchException("ElasticsearchException")),
    )
    response = client.post(
        f"{settings.indexation_path}/1",
        headers=TEST_HEADERS,
    )
    assert response.status_code == 500
    assert "Error: connection error" in response.text
    assert "ElasticsearchException" in response.text
