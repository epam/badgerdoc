from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from badgerdoc.models import workflow_registry


class WorkflowRegistryForm(forms.ModelForm):
    extraction_scope = forms.MultipleChoiceField(
        choices=workflow_registry.WorkflowRegistry.EXTRACTION_SCOPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select extraction scopes manually triggered workflow can process",
    )

    class Meta:
        model = workflow_registry.WorkflowRegistry
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        trigger = cleaned_data.get("trigger")
        event_entity = cleaned_data.get("event_entity")
        event_type = cleaned_data.get("event_type")

        if trigger == "automatic":
            if not event_entity:
                raise ValidationError(
                    {
                        "event_entity": "Event entity is required when trigger is set to automatic."
                    }
                )
            if not event_type:
                raise ValidationError(
                    {
                        "event_type": "Event type is required when trigger is set to automatic."
                    }
                )

        return cleaned_data

    def clean_extraction_scope(self):
        extraction_scope = self.cleaned_data.get("extraction_scope")
        if extraction_scope:
            return list(extraction_scope)
        return []


@admin.register(workflow_registry.WorkflowRegistry)
class WorkflowRegistryAdmin(admin.ModelAdmin):
    form = WorkflowRegistryForm
    list_display = (
        "id",
        "temporal_workflow_type",
        "event_entity",
        "event_type",
        "is_active",
        "trigger",
        "created_by",
        "created_at",
    )
    list_filter = (
        "event_entity",
        "event_type",
        "is_active",
        "trigger",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "temporal_workflow_type",
        "created_by__username",
        "temporal_queue",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_by", "created_at", "updated_at")

    fieldsets = (
        (
            "Workflow Configuration",
            {
                "fields": (
                    "temporal_workflow_type",
                    "temporal_queue",
                    "is_active",
                )
            },
        ),
        (
            "Trigger Configuration",
            {
                "fields": (
                    "trigger",
                    "event_entity",
                    "event_type",
                    "document_types",
                    "entity_tags",
                    "extraction_scope",
                    "support_prompts",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Metadata", {"fields": ("created_by",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        if not obj.document_types:
            obj.document_types = []
        if not obj.entity_tags:
            obj.entity_tags = []
        if not obj.extraction_scope:
            obj.extraction_scope = []
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by")
