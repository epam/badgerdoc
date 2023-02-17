from dev_runner.conf import settings

from .base_runner import BaseRunner


class AnnotationRunner(BaseRunner):
    PACKAGE_NAME = "annotation"
    APP_NAME = "annotation"
    PORT = settings.ANNOTATION_PORT
    DB_CREDENTIALS = {
        "POSTGRES_DB": "annotation",
    }
