import json
from typing import Tuple

import aiokafka
from kafka import admin, errors

from scheduler import config, log

logger = log.get_logger(__name__)


def create_topics() -> None:
    topic_list = []
    for topic_name, num_partitions, replication_factor in zip(
        config.KAFKA_CONSUME_TOPICS,
        config.KAFKA_TOPICS_PARTITIONS,
        config.KAFKA_REPLICATION_FACTORS,
    ):
        new_topic = admin.NewTopic(
            name=topic_name,
            num_partitions=int(num_partitions),
            replication_factor=int(replication_factor),
        )
        topic_list.append(new_topic)

    try:
        admin_client = admin.KafkaAdminClient(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVER,
        )
    except Exception:
        logger.exception("Failed to create KafkaAdminClient.")
        raise

    try:
        admin_client.create_topics(new_topics=topic_list)
    except errors.TopicAlreadyExistsError:
        logger.debug(
            f"At least one topic in topics "
            f"{config.KAFKA_CONSUME_TOPICS} already exists."
        )
        # It's ok if a topic already exists, continue without raising.
    else:
        logger.info(f"Topics {config.KAFKA_CONSUME_TOPICS} created.")


async def initialize_consumer() -> aiokafka.AIOKafkaConsumer:
    try:
        consumer = aiokafka.AIOKafkaConsumer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVER,
            group_id=config.KAFKA_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda v: json.loads(v.decode("ascii")),
            key_deserializer=lambda v: json.loads(v.decode("ascii")),
        )
    except Exception:
        logger.exception("Failed to initialize consumer.")
        raise
    consumer.subscribe(topics=config.KAFKA_CONSUME_TOPICS)
    logger.info(f"Consumer subscribed to topics {config.KAFKA_CONSUME_TOPICS}")
    return consumer


async def initialize_producer() -> aiokafka.AIOKafkaProducer:
    try:
        producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVER,
            value_serializer=lambda v: json.dumps(v).encode("ascii"),
            key_serializer=lambda v: json.dumps(v).encode("ascii"),
        )
    except Exception:
        logger.exception("Failed to initialize producer.")
        raise
    return producer


async def initialize_kafka() -> Tuple[
    aiokafka.AIOKafkaConsumer, aiokafka.AIOKafkaProducer
]:
    """Creates topics and initializes consumer and producer"""
    create_topics()
    consumer = await initialize_consumer()
    producer = await initialize_producer()
    return consumer, producer
