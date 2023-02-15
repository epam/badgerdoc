from .base_runner import BaseRunner
from dev_runner.conf import settings


class AssetsRunner(BaseRunner):
    PACKAGE_NAME = "assets"
    PORT = settings.ASSETS_PORT
    APP_NAME = "src"
    DB_CREDENTIALS = {
        "POSTGRES_DB": "file_management"
    }
    ENVIRONMENT = {
        "APP_NAME": "assets",
        "UPLOADING_LIMIT": "100",
        "WIDTH": "450",
        "BBOX_EXT": "20",
        "ROOT_PATH": "",
        "LOG_FILE": "False",
        "S3_PREFIX": "",
        "TEST_REGION": "us-west-2",
        "MINIO_SECURE_CONNECTION": "False",
        "SQLACLHEMY_POOL_SIZE": "DEBUG",
    }
