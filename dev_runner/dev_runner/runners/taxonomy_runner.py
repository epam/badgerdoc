from dev_runner.conf import settings

from .base_runner import BaseRunner


class TaxonomyRunner(BaseRunner):
    PACKAGE_NAME = "taxonomy"
    PORT = settings.TAXONOMY_PORT
    APP_NAME = "taxonomy"
    DB_CREDENTIALS = {
        "POSTGRES_DB": "taxonomy",
    }
    ENVIRONMENT = {
        "APP_HOST": "localhost",
        "APP_PORT": str(PORT),
    }
