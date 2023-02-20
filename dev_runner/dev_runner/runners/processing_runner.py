import logging

from dev_runner.conf import settings

from .base_runner import BaseRunner


class ProcessingRunner(BaseRunner):
    PACKAGE_NAME = "processing"
    PORT = settings.PROCESSING_PORT
    APP_NAME = "processing"
    DB_CREDENTIALS = {
        "POSTGRES_DB": "processing",
    }
    ENVIRONMENT = {
        "POSTGRES_DB": "processing",
        "MODELS_POSTFIX": "",
        "LOCAL_RUN": "1",
        "SERVICE_NAME": "processing",
        "HOST": "localhost",
        "PORT": str(PORT),
        "LOG_LEVEL": "10",
    }
