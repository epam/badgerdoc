from .base_runner import BaseRunner
from dev_runner.conf import settings


class ConvertRunner(BaseRunner):
    PACKAGE_NAME = "convert"
    PORT = settings.CONVERT_PORT
    APP_NAME = "src"
    ENVIRONMENT = {
        "IMPORT_COCO_URL": "http://0.0.0.0:8080/converter/import/"
    }
