from django.contrib import admin

from badgerdoc.models import task, task_extraction


class TaskExtractionInline(admin.TabularInline):
    model = task_extraction.TaskExtraction
    extra = 1
    fields = ("extraction",)


@admin.register(task.Task)
class TaskAdmin(admin.ModelAdmin):
    inlines = [TaskExtractionInline]
    list_display = ("id", "user", "status", "tags")
    list_filter = ("status", "user")
    search_fields = ("user__username",)
    ordering = ("-id",)
    readonly_fields = ("id",)

    fieldsets = (
        (
            "Task Information",
            {
                "fields": (
                    "id",
                    "user",
                    "document",
                    "status",
                    "tags",
                )
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "status")
