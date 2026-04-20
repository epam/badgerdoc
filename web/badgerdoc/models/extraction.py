from django.contrib.auth.models import User
from django.db import models
from django.db.models import TextChoices

from badgerdoc.models import _validation
from badgerdoc.models.base import TimestampedModel


class ExtractionStatus(TextChoices):
    STARTED = ("Started", "Started")
    IN_PROGRESS = ("In progress", "In progress")
    COMPLETED = ("Completed", "Completed")
    TIMED_OUT = ("Timed out", "Timed out")


_END_STATUSES = {
    ExtractionStatus.COMPLETED,
    ExtractionStatus.TIMED_OUT,
}


class Extraction(TimestampedModel):
    document = models.ForeignKey(
        "Document", on_delete=models.CASCADE, related_name="extractions"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="extractions"
    )
    status = models.CharField(
        max_length=20,
        choices=ExtractionStatus.choices,
        blank=True,
        null=True,
    )
    temporal_job_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Temporal workflow job ID for tracking",
    )
    comment = models.TextField(blank=True, null=True)
    tags = models.JSONField(
        blank=True,
        null=True,
        validators=[_validation.validate_tag_list],
        help_text="List of tags as strings",
    )

    class Meta:
        db_table = "extraction"
        ordering = ["-created_at"]
        permissions = [
            (
                "view_other_users_extractions",
                "Can view other users extractions",
            ),
        ]

    def __str__(self):
        if self.document:
            return f"Extraction {self.id} - {self.document}"
        return f"Extraction {self.id}"

    def is_in_progress(self):
        return self.status not in _END_STATUSES
