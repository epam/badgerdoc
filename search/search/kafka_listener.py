import json

from aiokafka import AIOKafkaConsumer
from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

from search.config import settings
from search.harvester import start_harvester
from search.logger import logger


async def create_topic() -> None:
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=settings.kafka_bootstrap_server
        )
        new_topics = [
            NewTopic(
                name=settings.kafka_search_topic,
                num_partitions=settings.kafka_search_topic_partitions,
                replication_factor=settings.kafka_search_replication_factor,
            )
        ]
        admin_client.create_topics(new_topics=new_topics)
    except TopicAlreadyExistsError:
        logger.info("Topic %s already exists", settings.kafka_search_topic)
    else:
        logger.info("Topic %s created", settings.kafka_search_topic)


async def consume() -> None:
    init_consumer = AIOKafkaConsumer(
        settings.kafka_search_topic,
        bootstrap_servers=settings.kafka_bootstrap_server,
        group_id=settings.kafka_group_id,
    )
    async with init_consumer as consumer:
        async for msg in consumer:
            try:
                message = json.loads(msg.value)
                await start_harvester(
                    message.get("tenant"),
                    message.get("job_id"),
                    message.get("file_id"),
                )
            except Exception:
                logger.exception(
                    "Error occurred during topic consumption. Topic: %s",
                    settings.kafka_search_topic,
                )
