import os

from django import forms
from django.contrib import admin

from badgerdoc.models import extraction


class ExtractionAdminForm(forms.ModelForm):
    class Meta:
        model = extraction.Extraction
        fields = "__all__"
        help_texts = {
            "tags": "JSON object containing list of strings",
            "document": "Search for document by ID or name. Start typing to see suggestions.",
        }


@admin.register(extraction.Extraction)
class ExtractionAdmin(admin.ModelAdmin):
    form = ExtractionAdminForm
    autocomplete_fields = ["document"]
    list_display = (
        "id",
        "document_id",
        "document_filename",
        "created_by",
        "status",
        "temporal_job_id",
        "created_at",
    )
    list_filter = ("status", "created_by", "created_at")
    search_fields = (
        "id",
        "temporal_job_id",
        "comment",
        "document__file",
        "document__name",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Extraction",
            {
                "fields": (
                    "document",
                    "created_by",
                    "status",
                    "temporal_job_id",
                    "comment",
                    "tags",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("document", "created_by")
        )

    def document_id(self, obj):
        if obj.document:
            return obj.document.id
        return "-"

    document_id.short_description = "Document ID"

    def document_filename(self, obj):
        if obj.document:
            doc_id = obj.document.id
            doc_name = obj.document.name or (
                os.path.basename(obj.document.file.name)
                if obj.document.file
                else f"Document {doc_id}"
            )
            return f"[{doc_id}] {doc_name}"
        return "-"

    document_filename.short_description = "Document"
