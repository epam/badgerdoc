import json

from django.contrib import admin
from django.utils.html import format_html

from badgerdoc.models.agent_log import AgentLog


@admin.register(AgentLog)
class AgentLogAdmin(admin.ModelAdmin):
    list_display = ("id", "document", "task", "level", "source", "created_at")
    list_filter = ("level", "source", "created_at")
    search_fields = ("document__id", "document__name")
    ordering = ("created_at",)
    readonly_fields = ("id", "log_pretty", "created_at")

    add_fieldsets = (
        (
            "Origin",
            {
                "fields": ("document", "task"),
            },
        ),
        (
            "Log",
            {
                "fields": ("level", "source", "log"),
            },
        ),
    )

    view_fieldsets = (
        (
            "Origin",
            {
                "fields": ("id", "document", "task", "created_at"),
            },
        ),
        (
            "Log",
            {
                "fields": ("level", "source", "log_pretty"),
            },
        ),
    )

    def get_readonly_fields(self, _request, obj=None):
        if obj is None:
            return ("id", "created_at")
        return (
            "id",
            "document",
            "task",
            "level",
            "source",
            "log_pretty",
            "created_at",
        )

    def get_fieldsets(self, _request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return self.view_fieldsets

    def log_pretty(self, obj):
        pretty = json.dumps(obj.log, indent=2, ensure_ascii=False)
        return format_html("<pre style='margin:0'>{}</pre>", pretty)

    log_pretty.short_description = "Log"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("document", "task")

    def has_change_permission(self, _request, _obj=None):
        return False
