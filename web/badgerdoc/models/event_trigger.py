from django.db import models

from badgerdoc.models.base import TimestampedModel


class EventTrigger(TimestampedModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    event_registry = models.ForeignKey(
        "WorkflowRegistry",
        on_delete=models.CASCADE,
        related_name="event_triggers",
        help_text="Workflow registry entry associated with this event trigger",
    )
    document = models.ForeignKey(
        "Document",
        on_delete=models.CASCADE,
        related_name="event_triggers",
        help_text="Document that triggered this event",
    )
    temporal_workflow_id = models.IntegerField(
        help_text="Temporal workflow identifier",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current status of the event trigger",
    )
    payload = models.JSONField(
        blank=True,
        null=True,
        help_text="Event payload data",
    )
    message = models.CharField(
        max_length=255,
        blank=True,
        help_text="Event message or description",
    )

    class Meta:
        db_table = "event_trigger"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Event {self.id} - {self.document.filename} - {self.status}"
