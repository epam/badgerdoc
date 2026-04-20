from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from badgerdoc.models import document, extraction


class ExtractionInline(admin.TabularInline):
    model = extraction.Extraction
    extra = 0
    fields = (
        "id",
        "created_by",
        "status",
        "temporal_job_id",
        "comment",
        "tags",
    )
    readonly_fields = ("id",)
    show_change_link = True
    verbose_name = "Extraction"
    verbose_name_plural = "Extractions"


@admin.register(document.Document)
class DocumentAdmin(admin.ModelAdmin):
    inlines = [ExtractionInline]
    list_display = (
        "id",
        "name",
        "extension",
        "tags",
        "uploaded_by",
        "children_count",
        "extractions_count",
        "created_at",
    )
    list_filter = ("extension", "uploaded_by", "created_at")
    search_fields = ("id", "name", "file", "extension")
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Document",
            {
                "fields": (
                    "name",
                    "file",
                    "extension",
                    "uploaded_by",
                    "parent_document",
                    "metadata",
                    "tags",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
        (
            "Children Documents",
            {"fields": ("children_list",), "classes": ("collapse",)},
        ),
        (
            "Extractions",
            {"fields": ("extractions_list",), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("uploaded_by")
            .prefetch_related("child_documents", "extractions")
        )

    def children_count(self, obj):
        count = len(obj.child_documents.all())
        if count > 0:
            return format_html(f"<strong>{count} children</strong>")
        return "No children"

    children_count.short_description = "Children"

    def children_list(self, obj):
        children = obj.child_documents.all()
        if not children:
            return "No child documents"

        links = []
        for child in children:
            url = reverse("admin:badgerdoc_document_change", args=[child.pk])
            name = child.name or f"Document {child.id}"
            links.append(format_html('<a href="{}">{}</a>', url, name))

        return format_html("<br>".join(links))

    children_list.short_description = "Child Documents"

    def extractions_count(self, obj):
        count = len(obj.extractions.all())
        if count > 0:
            return format_html(f"<strong>{count} extractions</strong>")
        return "No extractions"

    extractions_count.short_description = "Extractions"

    def extractions_list(self, obj):
        extractions = obj.extractions.all()
        if not extractions:
            return "No extractions"

        links = []
        for ext in extractions:
            url = reverse("admin:badgerdoc_extraction_change", args=[ext.pk])
            status = ext.status or "N/A"
            links.append(
                format_html(
                    '<a href="{}">Extraction {} - {}</a>', url, ext.id, status
                )
            )

        return format_html("<br>".join(links))

    extractions_list.short_description = "Extractions"

    readonly_fields = (
        "created_at",
        "updated_at",
        "children_list",
        "extractions_list",
    )
