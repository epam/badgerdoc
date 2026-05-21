import os
from dataclasses import dataclass
from uuid import uuid4

from django.contrib.auth.models import User
from django.db import models

from badgerdoc.models import _validation
from badgerdoc.models.base import TimestampedModel


def document_upload_path(_instance, filename):
    return f"documents/{uuid4().hex}/{filename}"


@dataclass
class Page:
    page_num: int
    document: "Document"


class Document(TimestampedModel):
    name = models.CharField(
        max_length=1024, blank=True, null=True, help_text="Document name"
    )
    file = models.FileField(upload_to=document_upload_path, null=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="documents"
    )
    parent_document = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="child_documents",
    )
    metadata = models.JSONField(
        blank=True, null=True, help_text="Metadata for the document"
    )
    tags = models.JSONField(
        blank=True,
        null=True,
        validators=[_validation.validate_tag_list],
        help_text="List of tags as strings",
    )
    extension = models.CharField(
        max_length=8,
        blank=True,
        null=True,
        help_text="File extension",
    )

    class Meta:
        db_table = "document"
        ordering = ["-updated_at"]
        permissions = [
            (
                "view_other_users_document",
                "Can view other users document",
            ),
            (
                "can_delete_document",
                "Can delete document",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            filename = os.path.basename(self.file.name)
            name_without_ext = os.path.splitext(filename)[0]
            self.name = name_without_ext
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        children = self.child_documents.all()
        for child in children:
            child.delete()

        if self.file:
            parent_uses_same_file = (
                self.parent_document_id is not None
                and self.parent_document.file.name == self.file.name
            )
            if not parent_uses_same_file:
                self.file.delete(save=False)

        super().delete(*args, **kwargs)

    def __str__(self):
        doc_name = None
        if self.name:
            doc_name = self.name
        elif self.file:
            doc_name = os.path.basename(self.file.name)
        else:
            doc_name = f"Document {self.id}"

        return f"[{self.id}] {doc_name}"
