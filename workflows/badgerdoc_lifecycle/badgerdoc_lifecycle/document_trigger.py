import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Literal

from temporalio import workflow

from badgerdoc_common import (
    badgerdoc_event,
    helpers,
    hocr,
    trigger,
    workflow_execution,
)
from badgerdoc_common.activities import (
    document,
    extraction,
    task,
    workflow_registry,
)
from badgerdoc_lifecycle.activities import hocr_extraction

logger = logging.getLogger(__name__)


@dataclass
class DocumentTriggerWorkflowResult:
    state: Literal["success", "error"] = "success"
    message: str | None = None


class DocumentTriggerError(Exception):
    pass


@workflow.defn
class DocumentTriggerWorkflow:

    @workflow.run
    async def run(
        self, request_data: trigger.BadgerodocTrigger
    ) -> DocumentTriggerWorkflowResult:
        logger.info("Starting DocumentTriggerWorkflow")

        new_extraction = None
        try:
            workflow_ = await self.get_workflow(
                request_data.get("workflow_registry_id"),
            )
            document_ = await self.get_document(
                request_data.get("document_id")
            )
            task_obj = await self.get_task(
                request_data.get("task_id"), document_
            )
            linked_extractions = await self.get_extractions(
                request_data.get("linked_extraction_ids"), document_, task_obj
            )
            linked_extraction_pages = await self.get_extraction_pages(
                request_data.get("linked_extraction_pages")
            )
            linked_extraction_xpaths = await self.get_extraction_xpaths(
                request_data.get("linked_extraction_xpaths")
            )
            target_extraction = await self.create_extraction(document_, task_obj)
            trigger_params = trigger.DocumentTriggerParams(
                workflow=workflow_,
                original_document=document_,
                original_document_rendition=document_,
                original_task=task_obj,
                linked_extractions=linked_extractions,
                linked_extraction_pages=linked_extraction_pages,
                linked_extraction_xpaths=linked_extraction_xpaths,
                target_extraction=target_extraction,
                llm_params=request_data.get("llm_params"),
            )

            workflow_params = workflow_execution.BadgerdocWorkflowParams(
                workflow_type=workflow_.temporal_workflow_type,
                task_queue=workflow_.temporal_queue,
                workflow_id=f"trigger-workflow-{workflow_.id}-document-{document_.id}-{hashlib.md5(json.dumps(request_data, sort_keys=True).encode()).hexdigest()}",  # nosec B324 - MD5 used for non-cryptographic hash for unique workflow ID
                workflow_input=trigger_params,
                random_postfix=True,
            )
            child_workflow_id = await workflow_execution.run_child_workflow(
                workflow_params
            )
            logger.info("Workflow input: %s", workflow_params)

            workflow_results = (
                await workflow_execution.wait_for_workflows_concurrent_t(
                    [child_workflow_id], hocr.BadgerdocHOCRPageResult
                )
            )

            await self.process_hocr_results(workflow_results, new_extraction)

            await self.finish_extraction(new_extraction)
        except DocumentTriggerError as e:
            logger.exception("Unable to complete DocumentTriggerWorkflow")
            return DocumentTriggerWorkflowResult(state="error", message=str(e))
        finally:
            if new_extraction:
                await self.finish_extraction(new_extraction)

        logger.info("DocumentTriggerWorkflow completed successfully")
        return DocumentTriggerWorkflowResult()

    async def get_document(
        self, document_id: int | None
    ) -> document.BadgerdocDocument:
        if not document_id:
            raise DocumentTriggerError("document_id is required")

        try:
            return await workflow.execute_activity(
                document.badgerdoc_get_document,
                document_id,
                start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
            )
        except Exception as err:
            raise DocumentTriggerError(
                "No such document or no access to document"
            ) from err

    async def get_task(
        self, task_id: int | None, document_: document.BadgerdocDocument
    ) -> task.BadgerdocTask | None:
        if not task_id:
            return None

        try:
            task_obj = await workflow.execute_activity(
                task.badgerdoc_get_task,
                task_id,
                start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
            )
        except Exception as err:
            raise DocumentTriggerError(
                "No such task or no access to task"
            ) from err

        if task_obj.document_id != document_.id:
            raise DocumentTriggerError("Task is not assigned to this document")

        return task_obj

    async def get_document_to_ocr(
        self,
        parent_document: document.BadgerdocDocument,
        page_number: int | None,
        scope: str | None,
    ) -> document.BadgerdocDocument | None:
        if scope == "page":
            return await self._get_page_rendition(parent_document, page_number)
        if scope == "document":
            return await self._get_document_rendition(parent_document)
        if scope == "block":
            return await self._get_block_rendition(parent_document)
        raise DocumentTriggerError(f"Unsupported scope: {scope}")

    async def _get_page_rendition(
        self,
        parent_document: document.BadgerdocDocument,
        page_number: int | None,
    ) -> document.BadgerdocDocument | None:
        if not page_number:
            logger.warning(
                "No page_number provided for OCR document selection"
            )
            return None

        list_request = document.ListDocumentsRequest(
            parent_document_id=parent_document.id,
            tags=["rendition"],
            metadata_field={"page": page_number},
        )

        documents_response = await workflow.execute_activity(
            document.badgerdoc_list_documents,
            list_request,
            start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
            retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
        )

        documents = documents_response.documents
        if not documents:
            logger.warning(
                "No rendition document found for parent_document_id=%s, page=%s",
                parent_document.id,
                page_number,
            )
            return None

        if len(documents) > 1:
            logger.warning(
                "Multiple rendition documents found for parent_document_id=%s, page=%s. Found %d documents, using first one.",
                parent_document.id,
                page_number,
                len(documents),
            )

        selected_document = documents[0]
        logger.info(
            "Selected document for OCR: id=%s, name=%s, page=%s",
            selected_document.id,
            selected_document.name,
            page_number,
        )
        return selected_document

    async def _get_document_rendition(
        self, parent_document: document.BadgerdocDocument
    ) -> document.BadgerdocDocument | None:
        raise NotImplementedError(
            "Document scope rendition is not implemented"
        )

    async def _get_block_rendition(
        self, parent_document: document.BadgerdocDocument
    ) -> document.BadgerdocDocument | None:
        raise NotImplementedError("Block scope rendition is not implemented")

    async def get_extractions(
        self,
        extraction_ids: list[int] | None,
        document_: document.BadgerdocDocument,
        task_obj: task.BadgerdocTask | None,
    ) -> list[extraction.BadgerdocExtraction] | None:
        if not extraction_ids:
            return None

        extractions = []

        for extraction_id in extraction_ids:
            try:
                extraction_obj = await workflow.execute_activity(
                    extraction.badgerdoc_get_extraction,
                    extraction_id,
                    start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                    retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                )
            except Exception as err:
                raise DocumentTriggerError(
                    "No such extraction or no access to extraction"
                ) from err

            if extraction_obj.document_id != document_.id:
                raise DocumentTriggerError(
                    "Extraction is not assigned to this document"
                )

            if task_obj is not None:
                task_extraction_ids = [ext.id for ext in task_obj.extractions]
                if extraction_obj.id not in task_extraction_ids:
                    raise DocumentTriggerError(
                        "Extraction is not assigned to this task"
                    )
            extractions.append(extraction_obj)

        return extractions

    async def get_workflow(
        self, workflow_registry_id: int | None
    ) -> badgerdoc_event.BadgerdocWorkflow:
        if not workflow_registry_id:
            raise DocumentTriggerError("workflow_registry_id is required")

        try:
            workflow_obj = await workflow.execute_activity(
                workflow_registry.badgerdoc_get_workflow_by_id,
                workflow_registry_id,
                start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
            )
        except Exception as err:
            raise DocumentTriggerError(
                "No such workflow or workflow is not active"
            ) from err

        return workflow_obj

    async def get_extraction_pages(
        self,
        linked_extraction_pages_data: list[dict] | None,
    ) -> list[extraction.BadgerdocExtractionPage] | None:
        if not linked_extraction_pages_data:
            return None

        extraction_pages = []
        for page_data in linked_extraction_pages_data:
            try:
                page = await workflow.execute_activity(
                    extraction.badgerdoc_get_extraction_page,
                    page_data["id"],
                    start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                    retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                )
                extraction_pages.append(page)
            except Exception as err:
                logger.warning(
                    "Failed to fetch extraction page id=%s: %s",
                    page_data.get("id"),
                    err,
                )

        return extraction_pages if extraction_pages else None

    async def get_extraction_xpaths(
        self,
        linked_extraction_xpaths_data: list[dict] | None,
    ) -> list[extraction.BadgerdocExtractionXpath] | None:
        if not linked_extraction_xpaths_data:
            return None

        extraction_xpaths = []
        for xpath_data in linked_extraction_xpaths_data:
            try:
                page = await workflow.execute_activity(
                    extraction.badgerdoc_get_extraction_page_by_extraction_and_page,
                    extraction.GetExtractionPageByExtractionAndPageRequest(
                        extraction_id=xpath_data["extraction_id"],
                        page_number=xpath_data["page_number"],
                    ),
                    start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                    retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                )
                xpath_ref = extraction.BadgerdocExtractionXpath(
                    extraction_page=page,
                    xpath=xpath_data["xpath"],
                )
                extraction_xpaths.append(xpath_ref)
            except Exception as err:
                logger.warning(
                    "Failed to fetch extraction xpath for extraction_id=%s, page=%s: %s",
                    xpath_data.get("extraction_id"),
                    xpath_data.get("page_number"),
                    err,
                )

        return extraction_xpaths if extraction_xpaths else None

    async def create_extraction(
        self,
        document_: document.BadgerdocDocument,
        task_obj: task.BadgerdocTask | None,
    ) -> extraction.BadgerdocExtraction:
        try:
            extraction_request = extraction.CreateExtractionRequest(
                document_id=document_.id,
                task_id=task_obj.id if task_obj else None,
                temporal_job_id=workflow.info().workflow_id,
            )

            return await workflow.execute_activity(
                extraction.badgerdoc_create_extraction,
                extraction_request,
                start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
            )
        except Exception as err:
            raise DocumentTriggerError("Failed to create extraction") from err

    async def finish_extraction(
        self, extraction_obj: extraction.BadgerdocExtraction
    ) -> extraction.BadgerdocExtraction:
        try:
            finish_request = extraction.FinishExtractionRequest(
                extraction_id=extraction_obj.id
            )

            return await workflow.execute_activity(
                extraction.badgerdoc_finish_extraction,
                finish_request,
                start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
            )
        except Exception as err:
            raise DocumentTriggerError("Failed to finish extraction") from err

    async def process_hocr_results(
        self,
        workflow_results: list[hocr.BadgerdocHOCRPageResult],
        new_extraction: extraction.BadgerdocExtraction,
    ) -> None:
        async def create_page(h_ocr):
            try:
                await workflow.execute_activity(
                    hocr_extraction.create_extraction_page,
                    args=[new_extraction.id, h_ocr],
                    start_to_close_timeout=helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT,
                    retry_policy=helpers.BadgerdocRestAPIRetryPolicy,
                )
            except Exception:
                logger.exception(
                    "Unable to create extraction %s", new_extraction.id
                )

        await asyncio.gather(
            *[create_page(h_ocr) for h_ocr in workflow_results]
        )
