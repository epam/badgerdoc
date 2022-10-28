from unittest.mock import Mock, call, patch

import pytest

from search.config import settings
from search.kafka_listener import consume, create_topic


@pytest.mark.unittest
@patch("search.kafka_listener.KafkaAdminClient")
@patch("search.kafka_listener.NewTopic")
@pytest.mark.asyncio
async def test_passed_arguments(mock_new_topic, mock_admin_client):
    await create_topic()

    assert mock_new_topic.call_args == call(
        name=settings.kafka_search_topic,
        num_partitions=settings.kafka_search_topic_partitions,
        replication_factor=settings.kafka_search_replication_factor,
    )

    new_topics = [mock_new_topic()]
    mock_admin_client.return_value.create_topics.assert_called_once_with(
        new_topics=new_topics
    )


@pytest.mark.unittest
@pytest.mark.asyncio
async def test_create_topic_exist(monkeypatch, mock_admin_client_topic_exists):
    monkeypatch.setattr(
        "search.kafka_listener.KafkaAdminClient",
        Mock(return_value=mock_admin_client_topic_exists),
    )
    await create_topic()


@pytest.mark.unittest
@pytest.mark.asyncio
async def test_consume_right_message_format(
    monkeypatch, mock_consume, mock_start_harvester
):
    monkeypatch.setattr(
        "search.kafka_listener.AIOKafkaConsumer",
        Mock(return_value=mock_consume),
    )
    monkeypatch.setattr(
        "search.kafka_listener.start_harvester",
        Mock(return_value=mock_start_harvester({})),
    )
    await consume()


@pytest.mark.unittest
@pytest.mark.parametrize(
    "message",
    [
        "",
        [],
        (),
        1,
    ],
)
@pytest.mark.asyncio
async def test_consume_wrong_message_format(
    monkeypatch, mock_consume, mock_start_harvester, message
):
    monkeypatch.setattr(
        "search.kafka_listener.AIOKafkaConsumer",
        Mock(return_value=mock_consume),
    )
    monkeypatch.setattr(
        "search.kafka_listener.start_harvester",
        Mock(return_value=mock_start_harvester(message)),
    )
    await consume()
