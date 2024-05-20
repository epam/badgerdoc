import json

import boto3
import pytest
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from kafka.errors import TopicAlreadyExistsError
from moto import mock_s3
from tests.test_get import CHILD_CATEGORIES_DATA, TEST_DATA
from tests.test_harvester import (
    DOCS_IN_ES,
    INDEX_NAME,
    MANIFESTS,
    S3_FAIL_PAGES,
    S3_PAGES,
)

from search.config import settings
from search.es import INDEX_SETTINGS

BUCKET_NAME = INDEX_NAME


@pytest_asyncio.fixture
async def es():
    es_ = AsyncElasticsearch(
        hosts=settings.es_host_test, port=settings.es_port_test
    )
    yield es_
    await es_.indices.delete(index=INDEX_NAME)
    await es_.close()


@pytest_asyncio.fixture
async def index_test_data(monkeypatch) -> None:
    es_ = AsyncElasticsearch(
        hosts=settings.es_host_test, port=settings.es_port_test
    )
    monkeypatch.setattr("search.main.ES", es_)
    await es_.indices.create(index=INDEX_NAME, ignore=400, body=INDEX_SETTINGS)
    for test_object in TEST_DATA + list(CHILD_CATEGORIES_DATA.values()):
        await es_.index(index=INDEX_NAME, document=test_object)
    await es_.indices.refresh(index=INDEX_NAME)
    yield

    await es_.indices.delete(index=INDEX_NAME, ignore=[400, 404])
    await es_.close()


def prepare_correct_pages(s3: boto3.resource) -> None:
    upload_doc(s3, S3_PAGES[0], 1, 1, S3_PAGES[0]["id"])
    upload_doc(s3, S3_PAGES[1], 1, 2, S3_PAGES[1]["id"])
    upload_doc(s3, S3_PAGES[2], 1, 2, S3_PAGES[2]["id"])
    upload_doc(s3, S3_PAGES[3], 2, 1, S3_PAGES[3]["id"])
    for page in S3_FAIL_PAGES.values():
        upload_doc(s3, page, 1, 2, page["id"])


def prepare_fail_pages(s3: boto3.resource) -> None:
    for page in S3_FAIL_PAGES.values():
        upload_doc(s3, page, 1, 3, page["id"])


def prepare_correct_manifests(s3: boto3.resource) -> None:
    upload_doc(s3, MANIFESTS[0], 1, 1, "manifest")
    upload_doc(s3, MANIFESTS[1], 1, 2, "manifest")
    upload_doc(s3, MANIFESTS[2], 2, 1, "manifest")


def prepare_fail_manifests(s3: boto3.resource) -> None:
    upload_doc(s3, MANIFESTS[3], 1, 3, "manifest")
    upload_doc(s3, MANIFESTS[4], 1, 4, "manifest")
    upload_doc(s3, MANIFESTS[2], 2, 1, "manifest")


def upload_doc(
    s3_resource: boto3.resource,
    document: dict,
    job_id: int,
    file_id: int,
    name: str,
) -> None:
    key = f"{settings.s3_start_path}/{job_id}/{file_id}/{name}.json"
    s3_resource.Bucket(BUCKET_NAME).put_object(
        Body=json.dumps(document, ensure_ascii=False),
        Key=key,
    )


@pytest.fixture
def moto_s3() -> boto3.resource:
    with mock_s3():
        s3_resource = boto3.resource("s3")
        s3_resource.create_bucket(Bucket=BUCKET_NAME)
        prepare_correct_pages(s3_resource)
        prepare_correct_manifests(s3_resource)
        yield s3_resource


@pytest.fixture
def moto_s3_fail_cases() -> boto3.resource:
    with mock_s3():
        s3_resource = boto3.resource("s3")
        s3_resource.create_bucket(Bucket=BUCKET_NAME)
        prepare_fail_pages(s3_resource)
        prepare_fail_manifests(s3_resource)
        yield s3_resource


@pytest_asyncio.fixture
async def dump_es_docs_empty_s3(es) -> boto3.resource:
    for document in DOCS_IN_ES:
        await es.index(index=INDEX_NAME, body=document)
    await es.indices.refresh(index=INDEX_NAME)
    with mock_s3():
        s3_resource = boto3.resource("s3")
        s3_resource.create_bucket(Bucket=BUCKET_NAME)
        yield s3_resource


@pytest_asyncio.fixture
async def dump_es_docs_moto_s3(es) -> boto3.resource:
    for document in DOCS_IN_ES:
        await es.index(index=INDEX_NAME, body=document)
    await es.indices.refresh(index=INDEX_NAME)
    with mock_s3():
        s3_resource = boto3.resource("s3")
        s3_resource.create_bucket(Bucket=BUCKET_NAME)
        prepare_correct_pages(s3_resource)
        prepare_correct_manifests(s3_resource)
        yield s3_resource


@pytest.fixture
def drop_es_index(moto_s3) -> boto3.resource:
    yield moto_s3


@pytest_asyncio.fixture
async def drop_parametrized_index(
    moto_s3, request, monkeypatch
) -> boto3.resource:
    es_ = AsyncElasticsearch(
        hosts=settings.es_host_test, port=settings.es_port_test
    )
    monkeypatch.setattr("search.harvester.ES", es_)
    yield moto_s3
    await es_.indices.delete(index=request.param)
    await es_.close()


@pytest.fixture
def mock_admin_client_topic_exists():
    class MockAdminClient:
        def create_topics(self, new_topics):
            raise TopicAlreadyExistsError

    yield MockAdminClient()


@pytest.fixture
def mock_message():
    def set_message(message):
        class Message:
            def __init__(self, value):
                self.value = value

        return Message(message)

    yield set_message


@pytest.fixture
def mock_consume(mock_message):
    class MockConsumer:
        def __init__(self):
            self.message = [mock_message(b"{}")]

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb): ...

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self.message:
                raise StopAsyncIteration
            return self.message.pop()

    yield MockConsumer()


@pytest_asyncio.fixture()
async def mock_start_harvester():
    async def get_message(msg):
        msg.get("tenant")
        msg.get("job_id")
        msg.get("file_id")

    yield get_message
