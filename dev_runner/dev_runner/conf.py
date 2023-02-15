import os
from pydantic import BaseSettings


BASE_PORT = os.environ.get("BD_BASE_PORT", 8000)


class RunnersSettings(BaseSettings):
    ANNOTATION_PORT: int = BASE_PORT + 0
    ASSETS_PORT: int = BASE_PORT + 1
    CONVERT_PORT: int = BASE_PORT + 2
    JOBS_PORT: int = BASE_PORT + 3
    MODELS_PORT: int = BASE_PORT + 4
    PIPELINES_PORT: int = BASE_PORT + 5
    PROCESSING_PORT: int = BASE_PORT + 6
    SCHEDULER_PORT: int = BASE_PORT + 7
    SEARCH_PORT: int = BASE_PORT + 8
    TAXONOMY_PORT: int = BASE_PORT + 9
    USERS_PORT: int = BASE_PORT + 10


settings = RunnersSettings()