from django.urls import path

from badgerdoc.views import tag
from badgerdoc.views.agent_log import AgentLogView
from badgerdoc.views.document import (
    DocumentView,
    create_document,
    get_document_chunk,
    get_document_dzi,
    get_document_dzi_content,
    get_document_dzi_tile,
    get_document_rendition_page,
    get_document_renditions,
    list_documents,
)
from badgerdoc.views.extraction import (
    ExtractionView,
    create_extraction,
    list_extraction_tags,
    list_extractions,
)
from badgerdoc.views.extraction_document import ExtractionDocumentView
from badgerdoc.views.extraction_page import (
    ExtractionPageView,
    get_latest_extraction_page,
    get_latest_extraction_pages,
    list_extraction_pages,
)
from badgerdoc.views.task import (
    create_task,
    get_task_by_id,
    list_tasks,
    update_task,
)
from badgerdoc.views.task_status import (
    list_next_task_statuses,
    list_task_statuses,
)
from badgerdoc.views.user import get_current_user_info
from badgerdoc.views.workflow import (
    get_workflow_registry_by_id,
    workflow_registry_list,
    workflow_registry_manual_trigger,
    workflow_registry_trigger,
    workflow_status,
)

urlpatterns = [
    path("document/", create_document, name="document-upload"),
    path(
        "document/<int:document_id>/chunk/page/<int:page_num>/extraction/<int:extraction_id>/xpath/<path:xpath>",
        get_document_chunk,
        name="document-chunk",
    ),
    path(
        "document/<int:document_id>/",
        DocumentView.as_view(),
        name="document-get-or-update",
    ),
    path(
        "document/<int:document_id>/renditions/",
        get_document_renditions,
        name="document-renditions",
    ),
    path(
        "document/<int:document_id>/rendition-page/<int:page>/",
        get_document_rendition_page,
        name="document-rendition-page",
    ),
    path(
        "document/<int:document_id>/dzi/",
        get_document_dzi,
        name="document-dzi",
    ),
    path(
        "document/<int:document_id>/dzi/page/<int:page>/<str:name>/<str:dzi_name>.dzi",
        get_document_dzi_content,
        name="document-dzi-content",
    ),
    path(
        "document/<int:document_id>/dzi/page/<int:page>/<str:name>/<str:dzi_name>_files/<int:layer>/<str:position>.png",
        get_document_dzi_tile,
        name="document-dzi-tile",
    ),
    path("documents/", list_documents, name="document-list"),
    path(
        "document/<int:document_id>/extraction-page/latest/",
        get_latest_extraction_pages,
        name="document-latest-extraction-pages",
    ),
    path(
        "document/<int:document_id>/extraction-page/latest/<int:page_num>/",
        get_latest_extraction_page,
        name="document-latest-extraction-page",
    ),
    path("extraction/", create_extraction, name="extraction-create"),
    path(
        "extraction/<int:extraction_id>/",
        ExtractionView.as_view(),
        name="get-or-update-extraction-by-id",
    ),
    path("extractions/", list_extractions, name="extraction-list"),
    path(
        "extraction/tags/", list_extraction_tags, name="extraction-tags-list"
    ),
    path(
        "extraction/<int:extraction_id>/extraction-document/",
        ExtractionDocumentView.as_view(),
        name="extraction-document",
    ),
    path(
        "extraction-page/",
        ExtractionPageView.as_view(),
        name="extraction-page-create",
    ),
    path(
        "extraction-pages/", list_extraction_pages, name="extraction-page-list"
    ),
    path(
        "workflow-registry/",
        workflow_registry_list,
        name="workflow-registry-list",
    ),
    path(
        "workflow-registry/<int:workflow_registry_id>/",
        get_workflow_registry_by_id,
        name="workflow-registry-detail",
    ),
    path(
        "workflow-registry/trigger/<int:workflow_registry_id>/",
        workflow_registry_trigger,
        name="workflow-registry-trigger",
    ),
    path(
        "workflow-registry/manual-trigger/<int:workflow_registry_id>/",
        workflow_registry_manual_trigger,
        name="workflow-registry-manual-trigger",
    ),
    path(
        "workflow-registry/workflow/status/<str:workflow_id>/",
        workflow_status,
        name="workflow-registry-trigger",
    ),
    path("task/", create_task, name="task-create"),
    path("task/<int:task_id>/", update_task, name="task-update"),
    path(
        "task/<int:task_id>/details/",
        get_task_by_id,
        name="get-task-details-by-id",
    ),
    path("tasks/", list_tasks, name="task-list"),
    path("task/status/", list_task_statuses, name="list-all-task-statuses"),
    path(
        "task/status/next/<int:current_status_id>/",
        list_next_task_statuses,
        name="list-next-task-statuses",
    ),
    path("user/me", get_current_user_info, name="get-current-user-info"),
    path("agent-log/", AgentLogView.as_view(), name="agent-log"),
    path("tags", tag.list_tags, name="list-tags"),
]
