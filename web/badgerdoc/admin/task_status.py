from django.contrib import admin

from badgerdoc.models import task_status


@admin.register(task_status.TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "order")
    search_fields = ("name",)
    ordering = ("order",)
    readonly_fields = ("id",)

    fieldsets = (
        (
            "Task Status Information",
            {
                "fields": (
                    "id",
                    "name",
                )
            },
        ),
        (
            "Relations",
            {
                "fields": (
                    "parent",
                    "order",
                )
            },
        ),
    )
    list_display_links = ("id", "name")
