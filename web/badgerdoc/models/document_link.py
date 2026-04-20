from django.db import models


class DocumentLink(models.Model):
    LINK_TYPE_CHOICES = [
        ("related", "Related"),
        ("parent", "Parent"),
        ("child", "Child"),
        ("version", "Version"),
        ("duplicate", "Duplicate"),
        ("reference", "Reference"),
    ]

    source = models.ForeignKey(
        "Document",
        on_delete=models.CASCADE,
        related_name="outgoing_links",
        help_text="Source document in the relationship",
    )
    dest = models.ForeignKey(
        "Document",
        on_delete=models.CASCADE,
        related_name="incoming_links",
        help_text="Destination document in the relationship",
    )
    link_type = models.CharField(
        max_length=50,
        choices=LINK_TYPE_CHOICES,
        help_text="Type of relationship between documents",
    )

    class Meta:
        db_table = "document_link"
        unique_together = [["source", "dest", "link_type"]]

    def __str__(self):
        return f"{self.source} -> {self.dest} ({self.link_type})"
