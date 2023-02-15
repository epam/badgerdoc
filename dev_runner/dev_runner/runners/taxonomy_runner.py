from .base_runner import BaseRunner
from dev_runner.conf import settings


class TaxonomyRunner(BaseRunner):
    PACKAGE_NAME = "taxonomy"
    PORT = settings.TAXONOMY_PORT
    APP_NAME = "app"
    DB_CREDENTIALS = {
        "POSTGRES_DB": "taxonomy",
    }
    ENVIRONMENT = {
        "APP_HOST": "localhost",
        "APP_PORT": str(PORT),
    }
