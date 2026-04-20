import logging
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from badgerdoc_common import badgerdoc_event
from badgerdoc_common.activities import document, extraction

logger = logging.getLogger(__name__)


@workflow.defn
class BadgerdocExtractionExample:

    @workflow.run
    async def run(self, request_data: badgerdoc_event.BadgerdocEvent) -> Any:
        logger.info(
            "Starting BadgerDoc extraction example workflow for document %d",
            request_data.document_id,
        )

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=100),
            maximum_attempts=3,
        )

        document_id = request_data.document_id
        _ = await workflow.execute_activity(
            document.badgerdoc_get_document,
            document_id,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )

        try:
            extraction_request = extraction.CreateExtractionRequest(
                document_id=request_data.document_id,
                temporal_job_id=workflow.info().workflow_id,
                comment="Example extraction created by BadgerdocExtractionExample workflow",
            )

            try:
                extraction_result = await workflow.execute_activity(
                    extraction.badgerdoc_create_extraction,
                    extraction_request,
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=retry_policy,
                )
                logger.info(
                    "Created extraction with ID: %d", extraction_result.id
                )
            except Exception as e:
                logger.warning("Failed to create extraction: %s", str(e))
                raise

            page_content = {
                "extracted_text": "Sample extracted text from document",
                "confidence_score": 0.95,
                "extraction_method": "example_workflow",
                "metadata": {
                    "workflow_id": workflow.info().workflow_id,
                    "document_id": request_data.document_id,
                    "extraction_id": extraction_result.id,
                },
            }

            page_request = extraction.CreateExtractionPageRequest(
                extraction_id=extraction_result.id,
                page_number=1,
                content=page_content,
            )

            try:
                extraction_page = await workflow.execute_activity(
                    extraction.badgerdoc_create_extraction_page,
                    page_request,
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=retry_policy,
                )
                logger.info(
                    "Created extraction page with ID: %d", extraction_page.id
                )
            except Exception as e:
                logger.warning("Failed to create extraction page: %s", str(e))
                raise

            finish_request = extraction.FinishExtractionRequest(
                extraction_id=extraction_result.id
            )

            try:
                finished_extraction = await workflow.execute_activity(
                    extraction.badgerdoc_finish_extraction,
                    finish_request,
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=retry_policy,
                )
                logger.info(
                    "Finished extraction with status: %s",
                    finished_extraction.status,
                )
            except Exception as e:
                logger.warning("Failed to finish extraction: %s", str(e))
                raise

            try:
                latest_extraction_page = await workflow.execute_activity(
                    extraction.badgerdoc_get_latest_extraction_page,
                    args=[document_id, 1],
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=retry_policy,
                )
                logger.info(
                    "Retrieved latest extraction page with ID: %d",
                    latest_extraction_page.id,
                )
            except Exception as e:
                logger.warning(
                    "Failed to get latest extraction page: %s", str(e)
                )
                raise

            return {
                "extraction_id": extraction_result.id,
                "extraction_page_id": extraction_page.id,
                "latest_extraction_page_id": latest_extraction_page.id,
                "status": finished_extraction.status,
                "workflow_id": workflow.info().workflow_id,
            }

        except Exception as e:
            logger.warning(
                "Failed to complete extraction workflow: %s", str(e)
            )
            raise
