from django.db import models

from badgerdoc.models.base import TimestampedModel


class ExtractionDocument(TimestampedModel):
    extraction = models.OneToOneField(
        "Extraction",
        on_delete=models.CASCADE,
        related_name="extraction_document",
    )
    content = models.JSONField(
        default=dict, help_text="Extracted content stored as JSON"
    )

    class Meta:
        db_table = "extraction_document"
        ordering = ["extraction"]

    def __str__(self):
        return f"Extraction document {self.id} for extraction {self.extraction.id}"
