from dataclasses import dataclass


@dataclass
class BadgerdocWorkflow:
    """Dataclass representing a WorkflowRegistry instance."""

    id: int
    name: str | None
    tags: list[str] | None
    created_by: int | str | dict
    event_entity: str | None
    event_type: str | None
    document_types: list[str]
    entity_tags: list[str]
    temporal_workflow_type: str
    temporal_queue: str
    is_active: bool
    trigger: str
    extraction_scope: list[str]
    support_prompts: bool
    created_at: str
    updated_at: str


@dataclass
class BadgerdocEvent:
    """Event data passed to Temporal workflows."""

    event_entity: str
    event_type: str
    document_type: str | None
    document_id: int
    supported_workflows: list[BadgerdocWorkflow]
    task_id: int | None = None
    extraction_id: int | None = None
