from dev_runner.conf import settings

from .base_runner import BaseRunner


class ModelsRunner(BaseRunner):
    PACKAGE_NAME = "models"
    PORT = settings.MODELS_PORT
    APP_NAME = "models"
    DB_CREDENTIALS = {
        "POSTGRES_DB": "models",
    }
    ENVIRONMENT = {
        "DATABASE_URL": "postgresql+psycopg2://postgres:postgres@localhost:5432/models",
        "MODELS_NAMESPACE": "dev2",
        "DOMAIN_NAME": "localhost",
        "ALGORITHM": "RS256",
        "SECRET": "some_secret_key",
        "DOCKER_REGISTRY_URL": "localhost:5000",
    }
