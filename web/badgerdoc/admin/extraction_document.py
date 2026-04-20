import os

from django.contrib import admin

from badgerdoc.models import extraction_document


@admin.register(extraction_document.ExtractionDocument)
class ExtractionDocumentAdmin(admin.ModelAdmin):
    autocomplete_fields = ["extraction"]
    list_display = (
        "id",
        "extraction",
        "document_filename",
        "created_at",
    )
    list_filter = ("extraction", "created_at")
    search_fields = ("id", "extraction__id", "extraction__document__file")
    ordering = ("extraction",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Extraction Document",
            {"fields": ("extraction", "content")},
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
            .select_related("extraction", "extraction__document")
        )

    def document_filename(self, obj):
        if obj.extraction and obj.extraction.document:
            doc = obj.extraction.document
            doc_id = doc.id
            doc_name = doc.name or (
                os.path.basename(doc.file.name)
                if doc.file
                else f"Document {doc_id}"
            )
            return f"[{doc_id}] {doc_name}"
        return "-"

    document_filename.short_description = "Document"
