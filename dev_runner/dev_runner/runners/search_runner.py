from .base_runner import BaseRunner
from dev_runner.conf import settings


class SearchRunner(BaseRunner):
    PACKAGE_NAME = "search"
    PORT = settings.SEARCH_PORT
    APP_NAME = "search"
    ENVIRONMENT = {
        "S3_START_PATH": "annotation",
        "APP_TITLE": "Badgerdoc Search",
        "JOBS_SEARCH": "/jobs/search",
        "ANNOTATION_CATEGORIES": "/categories",
        "ANNOTATION_CATEGORIES_SEARCH": "/categories/search",
        "MANIFEST": "manifest.json",
        "TEXT_PIECES_PATH": "/pieces",
        "INDEXATION_PATH": "indexation",
        "COMPUTED_FIELDS": '["job_id", "category"]',
        "JWT_ALGORITHM": "RS256",
        "KAFKA_GROUP_ID": "search_group",
        "KAFKA_SEARCH_TOPIC": "search",
        "KAFKA_SEARCH_TOPIC_PARTITIONS": "50",
        "KAFKA_SEARCH_REPLICATION_FACTOR": "1",
    }
