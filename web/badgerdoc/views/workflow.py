import logging
from typing import Any
from uuid import uuid4

from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from badgerdoc import llm_params_parser, permissions, temporal_client
from badgerdoc.models import (
    document,
    extraction,
    extraction_page,
    task,
    workflow_registry,
)

logger = logging.getLogger(__name__)


def validate_manual_trigger(validated_data: dict[str, Any]) -> Response | None:
    scope = validated_data.get("scope")
    if not scope:
        return Response(
            {"error": "scope is required for manual workflows"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    valid_scopes = [
        choice[0]
        for choice in workflow_registry.WorkflowRegistry.EXTRACTION_SCOPE_CHOICES
    ]
    if scope not in valid_scopes:
        return Response(
            {
                "error": f"Invalid scope '{scope}'. Valid options: {', '.join(valid_scopes)}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    document_id = validated_data.get("document_id")
    if not document_id:
        return Response(
            {"error": "document_id is required for manual workflows"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if scope == "page" and not validated_data.get("page_number"):
        return Response(
            {"error": "page_number is required for page scope"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if scope == "extraction" and not validated_data.get("extraction_id"):
        return Response(
            {"error": "extraction_id is required for extraction scope"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    scope = validated_data.get("scope")
    if not scope:
        return Response(
            {"error": "scope is required for manual workflows"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    valid_scopes = [
        choice[0]
        for choice in workflow_registry.WorkflowRegistry.EXTRACTION_SCOPE_CHOICES
    ]
    if scope not in valid_scopes:
        return Response(
            {
                "error": f"Invalid scope '{scope}'. Valid options: {', '.join(valid_scopes)}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    document_id = validated_data.get("document_id")
    if not document_id:
        return Response(
            {"error": "document_id is required for manual workflows"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if scope == "page" and not validated_data.get("page_number"):
        return Response(
            {"error": "page_number is required for page scope"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if scope == "extraction" and not validated_data.get("extraction_id"):
        return Response(
            {"error": "extraction_id is required for extraction scope"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None


def validate_automatic_trigger(
    validated_data: dict[str, Any],
) -> Response | None:
    if not validated_data.get("event_type"):
        return Response(
            {"error": "event_type is required for automatic workflows"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not validated_data.get("event_entity"):
        return Response(
            {"error": "event_entity is required for automatic workflows"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None


def start_automatic_workflow(registry, validated_data: dict[str, Any]) -> str:
    event: dict[str, Any] = validated_data
    event_entity = event.get("event_entity", "unknown")
    entity_id = (
        event.get("document_id")
        or event.get("task_id")
        or event.get("extraction_id")
        or "none"
    )

    trigger_type = registry.trigger
    workflow_id = f"{trigger_type}-{registry.temporal_workflow_type}-{registry.id}-{event_entity}-{entity_id}-{uuid4().hex[:5]}"
    temporal_client.start_workflow(
        workflow_type=registry.temporal_workflow_type,
        task_queue=registry.temporal_queue,
        workflow_id=workflow_id,
        args=[event],
    )

    return workflow_id


def start_manual_workflow(registry, validated_data: dict[str, Any]) -> str:
    trigger_data = {
        "scope": validated_data.get("scope"),
        "document_id": validated_data.get("document_id"),
        "workflow_registry_id": registry.id,
        "task_id": validated_data.get("task_id"),
        "page_number": validated_data.get("page_number"),
        "extraction_id": validated_data.get("extraction_id"),
        "llm_params": (
            validated_data.get("parameters", {}).get("llm_params")
            if validated_data.get("parameters")
            else None
        ),
    }

    workflow_id = f"manual-DocumentTriggerWorkflow-{registry.id}-{trigger_data['document_id']}-{uuid4().hex[:5]}"
    temporal_client.start_workflow(
        workflow_type="DocumentTriggerWorkflow",
        task_queue="badgerdoc_lifecycle",
        workflow_id=workflow_id,
        args=[trigger_data],
    )

    return workflow_id


class WorkflowRegistrySerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = workflow_registry.WorkflowRegistry
        fields = [
            "id",
            "name",
            "created_by",
            "event_entity",
            "event_type",
            "document_types",
            "entity_tags",
            "tags",
            "temporal_workflow_type",
            "temporal_queue",
            "is_active",
            "trigger",
            "extraction_scope",
            "support_prompts",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def validate_document_types(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Document types must be a list.")
        return value

    def validate_entity_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Entity tags must be a list.")
        return value

    def validate_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("All tags must be strings.")
        return value

    def validate_extraction_scope(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Extraction scope must be a list."
            )
        valid_scopes = ["document", "page", "extraction"]
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError(
                    "All extraction scopes must be strings."
                )
            if item not in valid_scopes:
                raise serializers.ValidationError(
                    f"Invalid extraction scope '{item}'. Valid options: Document, Page, Extraction."
                )
        return value


class WorkflowEventCommonFields(serializers.Serializer):
    event_type = serializers.ChoiceField(
        choices=["on_create", "on_update"], required=False
    )
    event_entity = serializers.ChoiceField(
        choices=[
            "document",
            "task",
            "extraction",
            "extraction_page",
            "extraction_document",
        ],
        required=False,
    )
    parameters = serializers.JSONField(required=False)


class WorkflowTriggerBaseSerializer(WorkflowEventCommonFields):
    document_id = serializers.IntegerField(required=False)
    task_id = serializers.IntegerField(required=False)
    extraction_id = serializers.IntegerField(required=False)
    page_number = serializers.IntegerField(required=False)
    scope = serializers.CharField(required=False)

    def validate(self, attrs):
        params = attrs.get("parameters")
        if params is not None and not isinstance(params, dict):
            raise serializers.ValidationError(
                {"parameters": "Parameters must be a JSON object (dict)."}
            )

        return attrs

    def validate_document_id(self, value: int) -> int:
        if not document.Document.objects.filter(id=value).exists():
            raise serializers.ValidationError("Document not found.")
        return value


class ManualWorkflowTriggerSerializer(serializers.Serializer):
    document_id = serializers.IntegerField(required=True)
    task_id = serializers.IntegerField(required=False, allow_null=True)
    llm_params = serializers.CharField(required=True, allow_blank=False)

    def validate_document_id(self, value: int) -> int:
        try:
            doc = document.Document.objects.get(id=value)
        except document.Document.DoesNotExist:
            raise serializers.ValidationError("Document not found.")

        request = self.context.get("request")
        if request and request.user:
            if doc.uploaded_by != request.user and not permissions.can_view_other_users_document(request.user):
                raise serializers.ValidationError("No permission to access this document.")

        return value

    def validate_task_id(self, value: int | None) -> int | None:
        if value is None:
            return value

        try:
            task_obj = task.Task.objects.get(id=value)
        except task.Task.DoesNotExist:
            raise serializers.ValidationError("Task not found.")

        request = self.context.get("request")
        if request and request.user:
            if task_obj.user != request.user and not permissions.can_view_other_users_tasks(request.user):
                raise serializers.ValidationError("No permission to access this task.")

        return value


class DocumentEventSerializer(WorkflowEventCommonFields):
    document_id = serializers.IntegerField(required=True)


class TaskEventSerializer(WorkflowEventCommonFields):
    document_id = serializers.IntegerField(required=True)
    task_id = serializers.IntegerField(required=True)

    def validate_task_id(self, value: int) -> int:
        task_ = task.Task.objects.filter(id=value).first()
        if not task_:
            raise serializers.ValidationError(
                f"Task with pk {value} not found."
            )

        if task_.document_id != self.initial_data["document_id"]:
            raise serializers.ValidationError(
                "Task must belong to the provided document_id."
            )

        return value


class ExtractionEventSerializer(WorkflowEventCommonFields):
    document_id = serializers.IntegerField(required=True)
    extraction_id = serializers.IntegerField(required=True)

    def validate_extraction_id(self, value: int) -> int:
        extraction_ = extraction.Extraction.objects.filter(id=value).first()
        if not extraction_:
            raise serializers.ValidationError(
                f"Extraction with pk {value} not found."
            )

        if extraction_.document_id != self.initial_data["document_id"]:
            raise serializers.ValidationError(
                "Extraction must belong to the provided document_id."
            )

        return value


class ExtractionPageEventSerializer(WorkflowEventCommonFields):
    document_id = serializers.IntegerField(required=True)
    extraction_id = serializers.IntegerField(required=True)
    page_number = serializers.IntegerField(required=True)

    def validate_extraction_id(self, value: int) -> int:
        extraction_ = extraction.Extraction.objects.filter(id=value).first()
        if not extraction_:
            raise serializers.ValidationError(
                f"Extraction with pk {value} not found."
            )

        if extraction_.document_id != self.initial_data["document_id"]:
            raise serializers.ValidationError(
                "Extraction must belong to the provided document_id."
            )

        return value

    def validate_page_number(self, value: int) -> int:
        extraction_id = self.initial_data.get("extraction_id")
        if not extraction_page.ExtractionPage.objects.filter(
            extraction_id=extraction_id, page_number=value
        ).exists():
            raise serializers.ValidationError(
                "Extraction page not found for the given extraction and page_number."
            )

        return value


class ExtractionDocumentEventSerializer(WorkflowEventCommonFields):
    document_id = serializers.IntegerField(required=True)
    extraction_id = serializers.IntegerField(required=True)

    def validate_extraction_id(self, value: int) -> int:
        extraction_ = extraction.Extraction.objects.filter(id=value).first()
        if not extraction_:
            raise serializers.ValidationError(
                f"Extraction with pk {value} not found."
            )

        if extraction_.document_id != self.initial_data["document_id"]:
            raise serializers.ValidationError(
                "Extraction must belong to the provided document_id."
            )

        if not getattr(extraction_, "extraction_document", None):
            raise serializers.ValidationError(
                "Extraction must have an associated extraction_document."
            )

        return value


@swagger_auto_schema(
    method="post",
    operation_description=(
        "Trigger a registered workflow. For automatic workflows, event_type and event_entity are required. "
        "For manual workflows, scope is required."
    ),
    operation_summary="Trigger Workflow Registry entry",
    tags=["Workflow Registry"],
    request_body=WorkflowTriggerBaseSerializer,
    responses={
        200: openapi.Response(
            description="Workflow started",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "workflow_id": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="ID of the triggered workflow",
                    ),
                },
            ),
        ),
        400: "Bad Request - validation error or inactive workflow",
        401: "Unauthorized - Authentication required",
        404: "Not Found - Workflow registry entry not found",
        500: "Internal Server Error - Failed to start workflow",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def workflow_registry_trigger(
    request: Request, workflow_registry_id: int
) -> Response[dict[str, Any]]:
    try:
        registry = workflow_registry.WorkflowRegistry.objects.filter(
            id=workflow_registry_id
        ).first()
        if not registry:
            return Response(
                {"error": "Workflow registry entry not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not registry.is_active:
            return Response(
                {"error": "Workflow is not active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_serializer = WorkflowTriggerBaseSerializer(
            data=request.data or {}
        )
        if not base_serializer.is_valid():
            return Response(
                base_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = base_serializer.validated_data

        if registry.trigger == "automatic":
            error_response = validate_automatic_trigger(validated_data)
            if error_response:
                return error_response
            workflow_id = start_automatic_workflow(registry, validated_data)
        elif registry.trigger == "manual":
            error_response = validate_manual_trigger(validated_data)
            if error_response:
                return error_response
            workflow_id = start_manual_workflow(registry, validated_data)
        else:
            return Response(
                {"error": "Invalid trigger type"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            "Triggered workflow %s for registry %s",
            workflow_id,
            registry.id,
        )

        return Response(
            {"workflow_id": workflow_id},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.exception(
            "Failed to manually trigger workflow registry %s",
            workflow_registry_id,
        )
        return Response(
            {"error": f"Failed to start workflow: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="post",
    operation_description="Trigger a manual workflow with document context parsed from llm_params",
    operation_summary="Manual Workflow Trigger",
    tags=["Workflow Registry"],
    request_body=ManualWorkflowTriggerSerializer,
    responses={
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Status of the request",
                    ),
                },
            ),
        ),
        400: "Bad Request - validation error",
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def workflow_registry_manual_trigger(
    request: Request, workflow_registry_id: int
) -> Response[dict[str, Any]]:
    try:
        serializer = ManualWorkflowTriggerSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        llm_params = validated_data.get("llm_params")

        parsed_params = llm_params_parser.parse(request.user.id, llm_params)

        response_data = {
            "linked_documents": [
                {"id": doc.id, "name": doc.name} for doc in parsed_params.linked_documents
            ],
            "linked_extractions": (
                [{"id": ext.id} for ext in parsed_params.linked_extractions]
                if parsed_params.linked_extractions
                else None
            ),
            "linked_extraction_pages": (
                [
                    {
                        "id": page.id,
                        "extraction_id": page.extraction_id,
                        "page_number": page.page_number,
                    }
                    for page in parsed_params.linked_extraction_pages
                ]
                if parsed_params.linked_extraction_pages
                else None
            ),
            "linked_extraction_xpaths": (
                [
                    {
                        "extraction_id": xpath.extraction_page.extraction_id,
                        "page_number": xpath.extraction_page.page_number,
                        "xpath": xpath.xpath,
                    }
                    for xpath in parsed_params.linked_extraction_xpaths
                ]
                if parsed_params.linked_extraction_xpaths
                else None
            ),
            "prompt_text": parsed_params.prompt_text,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(
            "Failed to parse llm_params for workflow registry %s",
            workflow_registry_id,
        )
        return Response(
            {"error": f"Failed to parse llm_params: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )




@swagger_auto_schema(
    method="get",
    operation_description="Get list of available workflows from Temporal registry",
    operation_summary="Workflow Registry Filter",
    tags=["Workflow Registry"],
    manual_parameters=[
        openapi.Parameter(
            "event_entity",
            openapi.IN_QUERY,
            description="Filter workflows by event entity",
            type=openapi.TYPE_STRING,
            required=False,
        ),
        openapi.Parameter(
            "event_type",
            openapi.IN_QUERY,
            description="Filter workflows by event type",
            type=openapi.TYPE_STRING,
            required=False,
        ),
        openapi.Parameter(
            "is_active",
            openapi.IN_QUERY,
            description="Filter workflows by active status (default: true)",
            type=openapi.TYPE_BOOLEAN,
            required=False,
            default=True,
        ),
        openapi.Parameter(
            "trigger",
            openapi.IN_QUERY,
            description="Filter workflows by trigger type (automatic or manual)",
            type=openapi.TYPE_STRING,
            required=False,
        ),
        openapi.Parameter(
            "extraction_scope",
            openapi.IN_QUERY,
            description="Filter workflows by extraction scope (comma-separated list). Returns workflows with at least one matching scope.",
            type=openapi.TYPE_STRING,
            required=False,
        ),
        openapi.Parameter(
            "tags",
            openapi.IN_QUERY,
            description="Filter workflows by tags (comma-separated list). Returns workflows with at least one matching tag.",
            type=openapi.TYPE_STRING,
            required=False,
        ),
    ],
    responses={
        200: openapi.Response(
            description="List of filtered workflows",
            schema=WorkflowRegistrySerializer(many=True),
        ),
        500: "Internal Server Error - Failed to connect to Temporal",
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def workflow_registry_list(request: Request) -> Response[dict[str, Any]]:
    try:
        is_active = request.GET.get("is_active", "true").lower() == "true"
        queryset = workflow_registry.WorkflowRegistry.objects.filter(
            is_active=is_active
        )

        trigger = request.GET.get("trigger")
        if trigger:
            queryset = queryset.filter(trigger=trigger)

        event_entity = request.GET.get("event_entity")
        if event_entity:
            queryset = queryset.filter(event_entity=event_entity)

        event_type = request.GET.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        extraction_scope = request.GET.get("extraction_scope")
        if extraction_scope:
            scope_list = [
                scope.strip() for scope in extraction_scope.split(",")
            ]
            q_objects = Q()
            for scope in scope_list:
                q_objects |= Q(extraction_scope__contains=[scope])
            queryset = queryset.filter(q_objects)

        tags = request.GET.get("tags")
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            if tag_list:
                q_objects = Q()
                for tag in tag_list:
                    q_objects |= Q(tags__contains=[tag])
                queryset = queryset.filter(q_objects)

        queryset = queryset.order_by("-created_at")

        serializer = WorkflowRegistrySerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": f"Failed to fetch workflow registries: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description="Get status of a workflow by id",
    operation_summary="Get Workflow Status",
    tags=["Workflow Registry"],
    manual_parameters=[
        openapi.Parameter(
            "workflow_id",
            openapi.IN_PATH,
            description="Temporal workflow id",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ],
    responses={
        200: openapi.Response(
            description="Workflow status",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        enum=["In Progress", "Finished", "Failed"],
                    ),
                },
            ),
        ),
        404: "Not Found - Workflow not found",
        500: "Internal Server Error",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def workflow_status(_: Request, workflow_id: str) -> Response:
    try:
        wf_status = temporal_client.get_workflow_status(workflow_id)
        if wf_status == temporal_client.TemporalWorkflowStatus.NOT_FOUND:
            return Response(
                {"error": "Workflow not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"status": wf_status.value}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Failed to get workflow status")
        return Response(
            {"error": f"Failed to get workflow status: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description="Get workflow registry by ID",
    tags=["Workflow Registry"],
    responses={
        200: "Workflow registry information",
        404: "Not Found - Workflow registry not found",
        500: "Internal Server Error",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_workflow_registry_by_id(
    _: Request, workflow_registry_id: int
) -> Response:
    try:
        workflow = workflow_registry.WorkflowRegistry.objects.get(
            id=workflow_registry_id
        )
        serializer = WorkflowRegistrySerializer(workflow)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except workflow_registry.WorkflowRegistry.DoesNotExist:
        return Response(
            {"error": "Workflow registry not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to fetch workflow registry: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
