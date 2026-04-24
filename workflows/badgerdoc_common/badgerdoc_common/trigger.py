from dataclasses import dataclass
from typing import TypedDict

from badgerdoc_common import badgerdoc_event
from badgerdoc_common.activities import (
    document,
    extraction,
    task,
    workflow_registry,
)


@dataclass
class BadgerdocDocumentPage:
    page_num: int
    document: document.BadgerdocDocument


@dataclass
class DocumentTriggerParams:
    workflow: badgerdoc_event.BadgerdocWorkflow
    original_document: document.BadgerdocDocument
    original_task: task.BadgerdocTask | None
    linked_documents: list[document.BadgerdocDocument]
    linked_document_pages: list[BadgerdocDocumentPage]
    linked_extractions: list[extraction.BadgerdocExtraction] | None
    linked_extraction_pages: list[extraction.BadgerdocExtractionPage] | None
    linked_extraction_xpaths: list[extraction.BadgerdocExtractionXpath] | None
    target_extraction: extraction.BadgerdocExtraction
    llm_params: str
