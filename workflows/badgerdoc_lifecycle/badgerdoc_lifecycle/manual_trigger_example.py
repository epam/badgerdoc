import logging
from typing import Any

from temporalio import workflow

logger = logging.getLogger(__name__)


@workflow.defn
class ManualTriggerExampleWorkflow:

    @workflow.run
    async def run(self, params: dict[str, Any]) -> None:
        logger.info("Starting ManualTriggerExampleWorkflow")
        logger.info("Received parameters: %s", params)
        logger.info("ManualTriggerExampleWorkflow completed successfully")
