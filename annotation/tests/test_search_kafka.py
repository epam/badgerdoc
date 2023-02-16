from unittest import mock

import responses
from fastapi.testclient import TestClient
from kafka.errors import NoBrokersAvailable
from pytest import mark

from annotation.annotations import add_search_annotation_producer
from annotation.kafka_client import producers
from annotation.microservice_communication.assets_communication import (
    ASSETS_FILES_URL,
)
from annotation.models import Category, File, Job, ManualAnnotationTask, User
from annotation.schemas import (
    CategoryTypeSchema,
    JobStatusEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)
from tests.override_app_dependency import TEST_HEADERS, TEST_TENANT, app

from .consts import ANNOTATION_PATH

client = TestClient(app)

ANNOTATION_KAFKA_JOB_ID = 1
ANNOTATION_KAFKA_FILE_ID = 1
ANNOTATION_KAFKA_USER_ID = "17ec1df0-006d-4905-a902-fbd1ed99a49d"
ANNOTATION_KAFKA_TASK_ID = 1
PIPELINE_PAGE, MANUAL_PAGE = 1, 2

ANNOTATION_KAFKA_USER = User(user_id=ANNOTATION_KAFKA_USER_ID)
ANNOTATION_KAFKA_CATEGORY = Category(
    id="Test", name="Test", type=CategoryTypeSchema.box
)
ANNOTATION_KAFKA_FILE = File(
    file_id=ANNOTATION_KAFKA_FILE_ID,
    tenant=TEST_TENANT,
    job_id=ANNOTATION_KAFKA_JOB_ID,
    pages_number=2,
    distributed_annotating_pages=[1],
    annotated_pages=[1],
    distributed_validating_pages=[1],
    validated_pages=[1],
)
ANNOTATION_KAFKA_JOB = Job(
    job_id=ANNOTATION_KAFKA_JOB_ID,
    callback_url="http://www.test.com/test1",
    annotators=[ANNOTATION_KAFKA_USER],
    validators=[ANNOTATION_KAFKA_USER],
    validation_type=ValidationSchema.hierarchical,
    is_auto_distribution=False,
    categories=[ANNOTATION_KAFKA_CATEGORY],
    tenant=TEST_TENANT,
    status=JobStatusEnumSchema.in_progress,
)
ANNOTATION_KAFKA_TASK = ManualAnnotationTask(
    id=1,
    file_id=ANNOTATION_KAFKA_FILE_ID,
    pages=[MANUAL_PAGE],
    job_id=ANNOTATION_KAFKA_JOB_ID,
    user_id=ANNOTATION_KAFKA_USER_ID,
    is_validation=False,
    status=TaskStatusEnumSchema.ready,
)
ASSETS_RESPONSE = {
    "pagination": {
        "page_num": 1,
        "page_size": 15,
        "min_pages_left": 1,
        "total": 1,
        "has_more": False,
    },
    "data": [
        {
            "id": ANNOTATION_KAFKA_FILE_ID,
            "original_name": "some.pdf",
            "bucket": "merck",
            "size_in_bytes": 165887,
            "content_type": "image/png",
            "pages": 10,
            "last_modified": "2021-09-28T01:27:55",
            "path": f"files/{ANNOTATION_KAFKA_FILE_ID}/some.pdf",
            "datasets": [],
        },
    ],
}

DOC_FOR_SAVE_BY_PIPELINE = {
    "pipeline": 1,
    "pages": [
        {
            "page_num": PIPELINE_PAGE,
            "size": {"width": 0.0, "height": 0.0},
            "objs": [],
        }
    ],
}

DOC_FOR_SAVE_BY_USER = {
    "user": ANNOTATION_KAFKA_USER_ID,
    "pages": [
        {
            "page_num": MANUAL_PAGE,
            "size": {"width": 0.0, "height": 0.0},
            "objs": [],
        }
    ],
}


@mark.unittest
def test_kafka_connection_error(monkeypatch):
    """Tests that NoBrokersAvailable (subclass of KafkaError) exception
    is correctly handled and no producers added to KAFKA_PRODUCERS.
    """
    monkeypatch.setattr(
        "annotation.annotations.main.KafkaProducer",
        mock.Mock(side_effect=NoBrokersAvailable()),
    )
    add_search_annotation_producer()
    assert not producers.get("search_annotation")


class MockProducer:
    def __init__(self, bootstrap_servers, client_id, value_serializer):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.value_serializer = value_serializer


@mark.unittest
@mock.patch(target="annotation.annotations.main.KAFKA_BOOTSTRAP_SERVER", new="url_1")
@mock.patch(target="annotation.annotations.main.KafkaProducer", new=MockProducer)
def test_add_search_annotation_producer(monkeypatch):
    """Checks that "add_search_annotation_producer" function calls
    "_init_search_annotation_producer" which creates KafkaProducer with
    correct arguments passed. Also checks that KAFKA_PRODUCERS has correct
    KafkaProducer as value for "search_annotation" key.
    """
    add_search_annotation_producer()
    mock_producer = producers["search_annotation"]
    assert isinstance(mock_producer, MockProducer)
    assert mock_producer.client_id == "search_group"
    assert mock_producer.bootstrap_servers == "url_1"


@mark.unittest
def test_producer_startup_creation(monkeypatch):
    """Checks that producer creation automatically called on app startup."""
    mock_startup = mock.Mock()
    monkeypatch.setattr(
        "annotation.annotations.main._init_search_annotation_producer", mock_startup
    )
    with TestClient(app):
        mock_startup.assert_called_once()


@mark.integration
@responses.activate
@mark.parametrize(
    ["annotation_type_path", "doc_type"],
    [
        (
            f"{ANNOTATION_KAFKA_JOB_ID}/{ANNOTATION_KAFKA_FILE_ID}",
            DOC_FOR_SAVE_BY_PIPELINE,
        ),
        (f"{ANNOTATION_KAFKA_TASK_ID}", DOC_FOR_SAVE_BY_USER),
    ],
)
@mock.patch(target="annotation.annotations.main.KAFKA_SEARCH_TOPIC", new="test")
@mock.patch(target="annotation.annotations.main.KafkaProducer", new=mock.Mock())
def test_post_annotation_send_message(
    monkeypatch,
    empty_bucket,
    prepare_search_annotation_kafka,
    annotation_type_path,
    doc_type,
):
    """Tests that producer sent correct message when pipeline or user posts
    new annotation."""
    monkeypatch.setattr(
        "annotation.annotations.main.connect_s3",
        mock.Mock(return_value=empty_bucket),
    )
    responses.add(
        responses.POST,
        ASSETS_FILES_URL,
        json=ASSETS_RESPONSE,
        status=200,
        headers=TEST_HEADERS,
    )
    with TestClient(app):
        mock_producer = producers["search_annotation"]
        mock_producer.send = mock.Mock(return_value=1)
        response = client.post(
            f"{ANNOTATION_PATH}/{annotation_type_path}",
            json=doc_type,
            headers=TEST_HEADERS,
        )
    assert response.status_code == 201
    mock_producer.send.assert_called_with(
        topic="test",
        value={
            "job_id": ANNOTATION_KAFKA_JOB_ID,
            "file_id": ANNOTATION_KAFKA_FILE_ID,
            "tenant": TEST_TENANT,
        },
    )
