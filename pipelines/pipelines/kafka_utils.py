import json
from typing import Optional

import aiokafka
from kafka import admin, errors
from pipelines import config, log

logger = log.get_logger(__name__)


class Kafka:
    _consumer: Optional[aiokafka.AIOKafkaConsumer] = None
    _producer: Optional[aiokafka.AIOKafkaProducer] = None

    @property
    def consumer(self) -> aiokafka.AIOKafkaConsumer:
        if self._consumer is not None:
            return self._consumer
        try:
            consumer = aiokafka.AIOKafkaConsumer(
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVER,
                group_id=config.KAFKA_GROUP_ID,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                value_deserializer=lambda v: json.loads(v.decode("ascii")),
                key_deserializer=lambda v: json.loads(v.decode("ascii")),
            )
            self._consumer = consumer
        except Exception:
            logger.exception("Failed to initialize consumer.")
            raise
        self.consumer.subscribe(topics=[config.KAFKA_CONSUME_TOPIC])
        logger.info(
            f"Consumer subscribed to topic {config.KAFKA_CONSUME_TOPIC}"
        )
        return self._consumer

    @property
    def producer(self) -> aiokafka.AIOKafkaProducer:
        if self._producer is not None:
            return self._producer
        try:
            producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVER,
                value_serializer=lambda v: json.dumps(v).encode("ascii"),
                key_serializer=lambda v: json.dumps(v).encode("ascii"),
            )
            self._producer = producer
            return self._producer
        except Exception:
            logger.exception("Failed to initialize producer.")
            raise

    @staticmethod
    def create_topics() -> None:
        new_topic = admin.NewTopic(
            name=config.KAFKA_CONSUME_TOPIC,
            num_partitions=int(config.KAFKA_TOPICS_PARTITIONS),
            replication_factor=int(config.KAFKA_REPLICATION_FACTORS),
        )

        try:
            admin_client = admin.KafkaAdminClient(
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVER,
            )
        except Exception:
            logger.exception("Failed to create KafkaAdminClient.")
            raise

        try:
            admin_client.create_topics(new_topics=[new_topic])
        except errors.TopicAlreadyExistsError:
            logger.debug(f"Topic {config.KAFKA_CONSUME_TOPIC} already exists.")
            # It's ok if a topic already exists, continue without raising.
        else:
            logger.info(f"Topics {config.KAFKA_CONSUME_TOPIC} created.")
