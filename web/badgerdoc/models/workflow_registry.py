from django.contrib.auth import models as auth_models
from django.db import models

from badgerdoc.models import _validation, base


class WorkflowRegistry(base.TimestampedModel):
    EVENT_ENTITY_CHOICES = [
        ("document", "Document"),
        ("task", "Task"),
        ("extraction", "Extraction"),
        ("search_parameters", "Search Parameters"),
    ]

    EVENT_TYPE_CHOICES = [
        ("on_create", "On Create"),
        ("on_update", "On Update"),
    ]

    TRIGGER_CHOICES = [
        ("manual", "Manual"),
        ("automatic", "Automatic"),
    ]

    EXTRACTION_SCOPE_CHOICES = [
        ("document", "Document"),
        ("page", "Page"),
        ("extraction", "Extraction"),
    ]

    created_by = models.ForeignKey(
        auth_models.User,
        on_delete=models.CASCADE,
        related_name="workflow_registries",
        help_text="User who created this workflow registry entry",
    )
    event_entity = models.CharField(
        max_length=50,
        choices=EVENT_ENTITY_CHOICES,
        null=True,
        blank=True,
        help_text="Entity that triggers this workflow",
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="Type of event that triggers this workflow",
    )
    document_types = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array of document types this workflow can process",
    )
    entity_tags = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array of entity tags this workflow can process. Matches tags from the event_entity (document, task, or extraction)",
    )
    temporal_workflow_type = models.CharField(
        max_length=255,
        help_text="Temporal workflow type/class name",
    )
    temporal_queue = models.CharField(
        max_length=255,
        help_text="Temporal task queue name",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this workflow is active and can be triggered",
    )
    trigger = models.CharField(
        max_length=20,
        choices=TRIGGER_CHOICES,
        default="automatic",
        help_text="How this workflow should be triggered",
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Human-readable name for this workflow",
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array of tags related to this workflow",
    )
    extraction_scope = models.JSONField(
        default=list,
        blank=True,
        validators=[_validation.validate_extraction_scope_list],
        help_text="JSON array of extraction scopes this workflow can process (document, page, extraction)",
    )
    support_prompts = models.BooleanField(
        default=False,
        help_text="Whether this workflow supports additional user prompts",
    )

    class Meta:
        db_table = "workflow_registry"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["event_type"], name="idx_workflow_event_type"
            ),
            models.Index(fields=["is_active"], name="idx_workflow_is_active"),
            models.Index(
                fields=["event_type", "is_active"],
                name="idx_workflow_event_active",
            ),
        ]

    def __str__(self):
        return f"{self.temporal_workflow_type} - {self.get_event_type_display()} - {self.is_active}"


def get_registries(
    event_entity: str | None = None,
    event_type: str | None = None,
    document_types: list[str] | None = None,
    entity_tags: list[str] | None = None,
    temporal_workflow_type: str | None = None,
    temporal_queue: str | None = None,
    is_active: bool = True,
    trigger: str | None = None,
    extraction_scope: list[str] | None = None,
    support_prompts: bool | None = None,
) -> list[WorkflowRegistry]:
    """
    Retrieve WorkflowRegistry entries based on filter parameters.

    This function filters WorkflowRegistry objects by various criteria. For array fields
    (document_types, entity_tags, extraction_scope), it returns registries where ANY
    of the provided values exist in the registry's corresponding array field.

    Args:
        event_entity: Filter by entity that triggers the workflow (e.g., "document", "task")
        event_type: Filter by event type (e.g., "on_create", "on_update")
        document_types: List of document types to match. Returns registries where any of
            these types exist in the registry's document_types array, OR where the
            registry's document_types is None/empty (meaning it accepts any type)
        entity_tags: List of entity tags to match.
            - If None: tag filtering is skipped entirely (caller does not care about tags).
            - If []: entity has no tags; only registries with no entity_tags requirement are returned.
            - If non-empty: returns registries where any of these tags exist in the
              registry's entity_tags array, OR where the registry's entity_tags is
              None/empty (meaning it accepts any tags).
        temporal_workflow_type: Filter by Temporal workflow type/class name
        temporal_queue: Filter by Temporal task queue name
        is_active: Filter by active status (default: True)
        trigger: Filter by trigger type (e.g., "manual", "automatic")
        extraction_scope: List of extraction scopes to match. Returns registries where
            any of these scopes exist in the registry's extraction_scope array
        support_prompts: Filter by whether workflow supports additional user prompts

    Returns:
        List of WorkflowRegistry objects matching the filter criteria

    Example:
        >>> registries = get_registries(
        ...     event_entity="document",
        ...     document_types=["pdf", "png"],
        ...     is_active=True
        ... )
        >>> # Returns registries where document_types contains "pdf" OR "png"
        >>> # OR where document_types is None/empty (universal workflow)
    """
    queryset = WorkflowRegistry.objects.all()

    if event_entity is not None:
        queryset = queryset.filter(event_entity=event_entity)

    if event_type is not None:
        queryset = queryset.filter(event_type=event_type)

    if document_types is not None and len(document_types) > 0:
        q_objects = models.Q()
        for doc_type in document_types:
            q_objects |= models.Q(document_types__contains=[doc_type])
        q_objects |= models.Q(document_types__isnull=True) | models.Q(
            document_types=[]
        )
        queryset = queryset.filter(q_objects)

    if entity_tags is not None and len(entity_tags) > 0:
        q_objects = models.Q()
        for entity_tag in entity_tags:
            q_objects |= models.Q(entity_tags__contains=[entity_tag])
        q_objects |= models.Q(entity_tags__isnull=True) | models.Q(
            entity_tags=[]
        )
        queryset = queryset.filter(q_objects)
    elif entity_tags is not None:
        queryset = queryset.filter(
            models.Q(entity_tags__isnull=True) | models.Q(entity_tags=[])
        )

    if temporal_workflow_type is not None:
        queryset = queryset.filter(
            temporal_workflow_type=temporal_workflow_type
        )

    if temporal_queue is not None:
        queryset = queryset.filter(temporal_queue=temporal_queue)

    queryset = queryset.filter(is_active=is_active)

    if trigger is not None:
        queryset = queryset.filter(trigger=trigger)

    if extraction_scope is not None and len(extraction_scope) > 0:
        q_objects = models.Q()
        for scope in extraction_scope:
            q_objects |= models.Q(extraction_scope__contains=[scope])
        queryset = queryset.filter(q_objects)

    if support_prompts is not None:
        queryset = queryset.filter(support_prompts=support_prompts)

    return list(queryset)
