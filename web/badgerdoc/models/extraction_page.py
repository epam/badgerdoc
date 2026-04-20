from django.db import models

from badgerdoc.models.base import TimestampedModel


class ExtractionPage(TimestampedModel):
    extraction = models.ForeignKey(
        "Extraction", on_delete=models.CASCADE, related_name="pages"
    )
    page_number = models.PositiveIntegerField()
    content = models.TextField(
        default="", help_text="Extracted content stored as text"
    )

    class Meta:
        db_table = "extraction_page"
        ordering = ["extraction", "page_number"]
        unique_together = ["extraction", "page_number"]

    def __str__(self):
        return f"Page {self.page_number} - Extraction {self.extraction.id}"
