from .base_runner import BaseRunner
from dev_runner.conf import settings


class AnnotationRunner(BaseRunner):
    PACKAGE_NAME = "annotation"
    PORT = settings.ANNOTATION_PORT
    DB_CREDENTIALS = {
        "POSTGRES_DB": "annotation",
    }