from dev_runner.conf import settings

from .base_runner import BaseRunner


class PipelinesRunner(BaseRunner):
    PACKAGE_NAME = "pipelines"
    PORT = settings.PIPELINES_PORT
    APP_NAME = "pipelines"
    MODULE_NAME = "app"
    DB_CREDENTIALS = {
        "POSTGRES_DB": "pipelines",
    }
    ENVIRONMENT = {
        "HEARTBEAT_TIMEOUT": "15",
        "HEARTBEAT_THRESHOLD_MUL": "10",
        "RUNNER_TIMEOUT": "5",
        "MAX_WORKERS": "20",
        "DEBUG_MERGE": "True",
        "SA_POOL_SIZE": "40",
        "LOG_LEVEL": "DEBUG",
    }
