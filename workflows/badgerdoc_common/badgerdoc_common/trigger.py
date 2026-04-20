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
    scope: str
    document_id: int
    workflow_registry_id: int
    task_id: int | None
    page_number: int | None
    extraction_id: int | None
    llm_params: dict | None


@dataclass
class DocumentTriggerParams:
    workflow: badgerdoc_event.BadgerdocWorkflow
    original_document: document.BadgerdocDocument
    document_to_ocr: document.BadgerdocDocument
    task: task.BadgerdocTask | None
    prev_extractions: list[extraction.BadgerdocExtraction] | None
    new_extraction: extraction.BadgerdocExtraction
    badgerdoc_trigger_params: BadgerodocTrigger
