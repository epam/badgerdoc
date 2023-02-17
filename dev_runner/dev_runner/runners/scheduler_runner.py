from dev_runner.conf import settings

from .base_runner import BaseRunner


class SchedulerRunner(BaseRunner):
    PACKAGE_NAME = "scheduler"
    PORT = settings.SCHEDULER_PORT
    APP_NAME = "scheduler"
    MODULE_NAME = "app"
    DB_CREDENTIALS = {"POSTGRES_DB": "scheduler"}
    ENVIRONMENT = {
        "DB_NAME": "scheduler",
        "DB_URL": "postgresql+psycopg2://postgres:postgres@localhost:5432/scheduler",
        "TEST_MODE": "False",
        "SA_POOL_SIZE": "10",
        "KAFKA_BOOTSTRAP_SERVER": "localhost:9092",
        "KAFKA_GROUP_ID": "scheduler_group",
        "KAFKA_CONSUME_TOPICS": "pipelines",
        "KAFKA_TOPICS_PARTITIONS": "1",
        "KAFKA_REPLICATION_FACTORS": "1",
        "HEARTBEAT_TIMEOUT": "10",
        "THRESHOLD_MUL": "3",
        "LOG_LEVEL": "DEBUG",
    }
