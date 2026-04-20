import os

from django.contrib import admin

from badgerdoc.models import extraction_page


@admin.register(extraction_page.ExtractionPage)
class ExtractionPageAdmin(admin.ModelAdmin):
    autocomplete_fields = ["extraction"]
    list_display = (
        "id",
        "extraction",
        "document_filename",
        "page_number",
        "created_at",
    )
    list_filter = ("extraction", "page_number", "created_at")
    search_fields = (
        "id",
        "page_number",
        "extraction__id",
        "extraction__document__file",
    )
    ordering = ("extraction", "page_number")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Extraction Page",
            {"fields": ("extraction", "page_number", "content")},
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
