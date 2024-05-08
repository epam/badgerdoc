import logging
import os
from datetime import datetime

from databricks.sdk import WorkspaceClient

from pipelines.schemas import PipelineOut

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


DATABRICKS_SERVICE_SCHEME = os.getenv("DATABRICKS_SERVICE_SCHEME", "http")
DATABRICKS_SERVICE_HOST = os.getenv("DATABRICKS_SERVICE_HOST")
DATABRICKS_SERVICE_PORT = os.getenv("DATABRICKS_SERVICE_PORT")


def get_client() -> WorkspaceClient:
    url = f"{DATABRICKS_SERVICE_SCHEME}://{DATABRICKS_SERVICE_HOST}"
    if DATABRICKS_SERVICE_PORT:
        url = f"{url}:{DATABRICKS_SERVICE_PORT}"
    return WorkspaceClient(host=url, token=os.environ["DATABRICKS_KEY"])


def get_pipelines():
    client = get_client()
    pipelines = client.jobs.list()
    for pipeline in pipelines:
        print(pipeline)
        print(pipeline.settings)
        yield PipelineOut(
            type="databricks",
            is_latest=False,
            version=1,
            date=datetime.today(),  # todo: change to created_time
            meta={},
            steps=[],
            name=f"{pipeline.settings.name}:databricks",
            id=0,
        )
