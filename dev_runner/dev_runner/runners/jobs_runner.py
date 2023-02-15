from .base_runner import BaseRunner
from dev_runner.conf import settings


class JobsRunner(BaseRunner):
    PACKAGE_NAME = "jobs"
    PORT = settings.JOBS_PORT
    APP_NAME = "jobs"
    ENVIRONMENT = {
        "POSTGRESQL_JOBMANAGER_DATABASE_URI": "postgresql+psycopg2://postgres:postgres@localhost:5432/job_manager"
    }
