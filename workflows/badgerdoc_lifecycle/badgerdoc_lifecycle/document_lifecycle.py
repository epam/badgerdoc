import logging
from dataclasses import dataclass

from temporalio import workflow

from badgerdoc_common import workflow_execution
from badgerdoc_common.badgerdoc_event import BadgerdocEvent

logger = logging.getLogger(__name__)


@dataclass
class BadgerdocLifecycleDocumentWorkflowResult:
    pass


@workflow.defn
class BadgerdocLifecycleWorkflow:

    def generate_workflow_id(self, request_data: BadgerdocEvent) -> str:
        if request_data.event_entity == "document":
            event_entity_id = request_data.document_id
        elif request_data.event_entity == "task":
            event_entity_id = request_data.task_id
        elif request_data.event_entity == "extraction":
            event_entity_id = request_data.extraction_id
        else:
            event_entity_id = request_data.document_id

        return f"badgerdoc-lifecycle-document-{request_data.document_id}-{request_data.event_entity}-{request_data.event_type}-triggered-{event_entity_id}"

    @workflow.run
    async def run(
        self,
        request_data: BadgerdocEvent,
    ) -> BadgerdocLifecycleDocumentWorkflowResult:
        logger.info(
            "Starting BadgerDoc %s lifecycle workflow",
            request_data.event_entity,
        )

        started_workflow_ids = []
        for workflow_data in request_data.supported_workflows:
            logger.debug(
                "Trying to start workflow %s",
                workflow_data.temporal_workflow_type,
            )

            workflow_id = self.generate_workflow_id(request_data)
            params = workflow_execution.BadgerdocWorkflowParams(
                workflow_type=workflow_data.temporal_workflow_type,
                task_queue=workflow_data.temporal_queue,
                workflow_id=workflow_id,
                workflow_input=request_data,
                random_postfix=True,
            )
            workflow_id = await workflow_execution.run_child_workflow(params)
            logger.debug("Adding workflow to started_workflow_ids")
            started_workflow_ids.append(workflow_id)

        workflow_results = (
            await workflow_execution.wait_for_workflows_concurrent(
                started_workflow_ids
            )
        )

        logger.info("All workflows completed: %s", workflow_results)
        logger.info(
            "BadgerDoc %s lifecycle workflow completed successfully",
            request_data.event_entity,
        )
        return BadgerdocLifecycleDocumentWorkflowResult()
