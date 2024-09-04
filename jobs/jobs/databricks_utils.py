import dataclasses
import json
import logging
import os
from datetime import datetime
from typing import Iterator, List

from databricks.sdk import WorkspaceClient

import jobs.pipeline as pipeline
from jobs.schemas import Pipeline

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


def get_pipelines() -> Iterator[Pipeline]:
    client = get_client()
    pipelines = client.jobs.list()
    for pipeline_ in pipelines:
        yield Pipeline(
            id=pipeline_.job_id,
            type="databricks",
            version=1,
            date=datetime.today(),  # todo: change to created_time
            meta={},
            name=f"{pipeline_.settings.name}",
        )


async def run(
    pipeline_id: str,
    job_id: int,
    files: List[pipeline.PipelineFile],
    current_tenant: str,
    datasets: List[pipeline.Dataset],
) -> None:
    logger.info(
        "Running pipeline %s, job_id %s, current_tenant: %s with arguments %s",
        pipeline_id,
        job_id,
        current_tenant,
        files,
    )
    client = get_client()
    client.jobs.run_now(
        pipeline_id,
        job_parameters={
            "badgerdoc_job_parameters": json.dumps(
                dataclasses.asdict(
                    pipeline.PipelineRunArgs(
                        job_id=job_id,
                        tenant=current_tenant,
                        files_data=files,
                        datasets=datasets,
                    )
                )
            )
        },
    )


class DatabricksPipeline(pipeline.BasePipeline):
    async def list(self) -> List[pipeline.AnyPipeline]:
        # todo: bind to AnyPipeline
        return get_pipelines()

    async def run(
        self,
        pipeline_id: str,
        job_id: str,
        files: List[pipeline.PipelineFile],
        current_tenant: str,
        datasets: List[pipeline.Dataset],
    ) -> None:
        await run(
            pipeline_id, int(job_id), files, current_tenant, datasets=datasets
        )
