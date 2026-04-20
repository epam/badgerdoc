from django.contrib import admin

from badgerdoc.models import tag


@admin.register(tag.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("tag", "literal", "order")
    search_fields = ("literal",)
    ordering = ("order",)
    readonly_fields = ("id",)

    fieldsets = (
        (
            "Task Status Information",
            {
                "fields": (
                    "id",
                    "tag",
                    "literal",
                    "order",
                )
            },
        ),
    )
