from django.apps import AppConfig


class BadgerdocConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "badgerdoc"
    verbose_name = "BadgerDoc"

    def ready(self):
        ########################################################################
        # Import admin configurations for Django auto-discovery
        # ########################################################################
        from badgerdoc.admin.document import DocumentAdmin  # noqa: F401
        from badgerdoc.admin.extraction import ExtractionAdmin  # noqa: F401
        from badgerdoc.admin.extraction_document import (  # noqa: F401
            ExtractionDocumentAdmin,
        )
        from badgerdoc.admin.extraction_page import (  # noqa: F401
            ExtractionPageAdmin,
        )
        from badgerdoc.admin.tag import TagAdmin  # noqa: F401
        from badgerdoc.admin.task import TaskAdmin  # noqa: F401
        from badgerdoc.admin.task_status import TaskStatusAdmin  # noqa: F401
        from badgerdoc.admin.workflow import (  # noqa: F401
            WorkflowRegistryAdmin,
            WorkflowRegistryForm,
        )

        ########################################################################
        # Import signal handlers
        ########################################################################
        from badgerdoc.signals import trigger_automatic  # noqa: F401
