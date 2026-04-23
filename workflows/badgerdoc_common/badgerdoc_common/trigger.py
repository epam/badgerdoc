from dataclasses import dataclass
from typing import TypedDict

from badgerdoc_common import badgerdoc_event
from badgerdoc_common.activities import (
    document,
    extraction,
    task,
    workflow_registry,
)


class BadgerodocTrigger(TypedDict):
    document_id: int
    workflow_registry_id: int
    task_id: int | None
    llm_params: str
    linked_document_ids: list[int]
    linked_extraction_ids: list[int] | None
    linked_extraction_pages: list[dict] | None
    linked_extraction_xpaths: list[dict] | None


@dataclass
class DocumentTriggerParams:
    workflow: badgerdoc_event.BadgerdocWorkflow
    original_document: document.BadgerdocDocument
    original_document_rendition: document.BadgerdocDocument
    original_task: task.BadgerdocTask | None
    linked_extractions: list[extraction.BadgerdocExtraction] | None
    linked_extraction_pages: list[extraction.BadgerdocExtractionPage] | None
    linked_extraction_xpaths: list[extraction.BadgerdocExtractionXpath] | None
    target_extraction: extraction.BadgerdocExtraction
    llm_params: str
