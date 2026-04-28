from dataclasses import dataclass

from badgerdoc_common import badgerdoc_event
from badgerdoc_common.activities import (
    document,
    extraction,
    task,
)


@dataclass
class BadgerdocDocumentPage:
    page_num: int
    document: document.BadgerdocDocument


@dataclass
class DocumentTriggerParams:
    workflow: badgerdoc_event.BadgerdocWorkflow
    original_document: document.BadgerdocDocument
    target_extraction: extraction.BadgerdocExtraction
    llm_params: str
    original_task: task.BadgerdocTask | None = None
    linked_documents: list[document.BadgerdocDocument] | None = None
    linked_document_pages: list[BadgerdocDocumentPage] | None = None
    linked_extractions: list[extraction.BadgerdocExtraction] | None = None
    linked_extraction_pages: (
        list[extraction.BadgerdocExtractionPage] | None
    ) = None
    linked_extraction_xpaths: (
        list[extraction.BadgerdocExtractionXpath] | None
    ) = None
