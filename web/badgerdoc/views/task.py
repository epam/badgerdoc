import logging
from typing import Any

import django_filters
from django.db import models
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from badgerdoc import permissions
from badgerdoc.models import (
    document,
    extraction,
    task,
    task_extraction,
    task_status,
)
from badgerdoc.views import _pagination
from badgerdoc.views.task_status import TaskStatusSerializer

logger = logging.getLogger(__name__)


class TaskFilter(django_filters.FilterSet):
    status_id = django_filters.NumberFilter(field_name="status_id")
    user_id = django_filters.NumberFilter(field_name="user_id")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )
    updated_at__gte = django_filters.DateTimeFilter(
        field_name="updated_at", lookup_expr="gte"
    )
    updated_at__lte = django_filters.DateTimeFilter(
        field_name="updated_at", lookup_expr="lte"
    )

    class Meta:
        model = task.Task
        fields = []


class TaskDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = document.Document
        fields = ["id", "file", "metadata", "tags"]


class TaskExtractionSerializer(serializers.ModelSerializer):
    document_id = serializers.IntegerField(
        source="document.id", read_only=True
    )
    created_by = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = extraction.Extraction
        fields = [
            "id",
            "document_id",
            "created_by",
            "status",
            "temporal_job_id",
            "comment",
            "tags",
        ]


class TaskSerializer(serializers.ModelSerializer):
    status = TaskStatusSerializer()
    document = TaskDocumentSerializer()
    extractions = serializers.SerializerMethodField()

    class Meta:
        model = task.Task
        fields = [
            "id",
            "user",
            "status",
            "document",
            "extractions",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "document",
            "extractions",
            "tags",
            "created_at",
            "updated_at",
        ]

    def get_extractions(self, obj):
        task_extractions = obj.task_extractions.select_related("extraction")
        return TaskExtractionSerializer(
            [te.extraction for te in task_extractions], many=True
        ).data


PaginatedTaskSerializer = _pagination.build_paginated_serializer(
    TaskSerializer
)


class TaskUpdateSerializer(serializers.ModelSerializer):
    status = serializers.PrimaryKeyRelatedField(
        queryset=task_status.TaskStatus.objects.all(), required=True
    )
    extractions = serializers.PrimaryKeyRelatedField(
        queryset=extraction.Extraction.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = task.Task
        fields = ["status", "extractions", "tags", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def update(self, instance, validated_data):
        status_obj = validated_data.pop("status", None)
        extractions = validated_data.pop("extractions", [])

        if extractions:
            extraction_documents = {
                extraction_obj.document.id for extraction_obj in extractions
            }
            if len(extraction_documents) > 1 or (
                instance.document.id not in extraction_documents
            ):
                raise serializers.ValidationError(
                    "All extractions must belong to the same document as the task's document."
                )

            instance.task_extractions.all().delete()
            for extraction_obj in extractions:
                task_extraction.TaskExtraction.objects.create(
                    task=instance, extraction=extraction_obj
                )

        if status_obj:
            instance.status = status_obj

        instance.save()

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["id"] = instance.id
        data["user"] = instance.user.id
        data["status"] = TaskStatusSerializer(instance.status).data
        data["document"] = TaskDocumentSerializer(instance.document).data
        task_extractions = instance.task_extractions.select_related(
            "extraction"
        )
        data["extractions"] = TaskExtractionSerializer(
            [te.extraction for te in task_extractions], many=True
        ).data
        return data


class TaskCreateSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(
        queryset=document.Document.objects.all(),
        required=False,
        write_only=True,
    )
    extractions = serializers.PrimaryKeyRelatedField(
        queryset=extraction.Extraction.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )
    status = serializers.PrimaryKeyRelatedField(
        queryset=task_status.TaskStatus.objects.all(),
        required=False,
    )

    class Meta:
        model = task.Task
        fields = [
            "id",
            "user",
            "status",
            "document",
            "extractions",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        document_obj = attrs.get("document")
        extractions = attrs.get("extractions", [])

        if extractions:
            extraction_documents = {
                extraction_obj.document.id for extraction_obj in extractions
            }
            if len(extraction_documents) > 1:
                raise serializers.ValidationError(
                    "All extractions must refer to the same document."
                )

            for extraction_obj in extractions:
                if (
                    document_obj
                    and extraction_obj.document.id != document_obj.id
                ):
                    raise serializers.ValidationError(
                        "All extractions and provided document must refer to the same document."
                    )
                document_obj = extraction_obj.document

        if not document_obj:
            raise serializers.ValidationError(
                "Document is required to be set via 'extractions' or 'document'"
            )

        attrs["document"] = document_obj
        return attrs

    def create(self, validated_data: dict[str, Any]) -> task.Task:
        extractions = validated_data.pop("extractions", [])
        validated_data["user"] = self.context["request"].user

        if "status" not in validated_data:
            validated_data["status"] = (
                task_status.TaskStatus.objects.annotate(
                    parent_count=models.Count("parent")
                )
                .order_by("parent_count", "order")
                .first()
            )

        task_obj = super().create(validated_data)
        task_obj.save()

        for extraction_obj in extractions:
            task_extraction.TaskExtraction.objects.create(
                task=task_obj, extraction=extraction_obj
            )

        return task_obj

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["status"] = TaskStatusSerializer(instance.status).data
        task_extractions = instance.task_extractions.select_related(
            "extraction"
        )
        data["document"] = TaskDocumentSerializer(instance.document).data
        data["extractions"] = TaskExtractionSerializer(
            [te.extraction for te in task_extractions], many=True
        ).data
        return data


def get_task_queryset(user: Any) -> Any:
    queryset = (
        task.Task.objects.select_related("status", "document")
        .prefetch_related("task_extractions__extraction")
        .order_by("-created_at")
    )

    if not permissions.can_view_other_users_tasks(user):
        queryset = queryset.filter(user_id=user.id)

    return queryset


@swagger_auto_schema(
    method="post",
    operation_description=(
        "Create a new task with. "
        "A task must always be linked to a document. "
        "Provide the document directly or by linking an extraction, "
        "note that extraction's document must be the same as provided document if any."
    ),
    operation_summary="Create Task",
    tags=["Tasks"],
    request_body=TaskCreateSerializer,
    responses={
        201: openapi.Response(
            description="Task created successfully",
            schema=TaskCreateSerializer,
        ),
        400: "Bad Request - Invalid data",
        401: "Unauthorized - Authentication required",
        500: "Internal Server Error - Failed to create task",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_task(request: Request) -> Response:
    try:
        serializer = TaskCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except serializers.ValidationError as e:
        logger.exception("Validation error creating task")
        return Response(
            {"error": f"Validation error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception("Failed to create task")
        return Response(
            {"error": f"Failed to create task: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="patch",
    operation_description="Update task status",
    operation_summary="Update Task Status",
    tags=["Tasks"],
    request_body=TaskUpdateSerializer,
    responses={
        200: openapi.Response(
            description="Task status updated successfully",
            schema=TaskUpdateSerializer,
        ),
        400: "Bad Request - Invalid data",
        401: "Unauthorized - Authentication required",
        404: "Not Found - Task not found",
        500: "Internal Server Error - Failed to update task",
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_task(request: Request, task_id: int) -> Response:
    try:
        queryset = get_task_queryset(request.user)
        task_obj = queryset.get(id=task_id)
    except task.Task.DoesNotExist:
        return Response(
            {"error": "Task not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        serializer = TaskUpdateSerializer(
            task_obj, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
    except serializers.ValidationError as e:
        logger.exception("Validation error updating task")
        return Response(
            {"error": f"Validation error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception("Failed to update task")
        return Response(
            {"error": f"Failed to update task: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description=(
        "List tasks with filtering. By default, users can only see their own tasks. "
        "Staff users or users with 'view_other_users_tasks' permission can see all tasks."
    ),
    operation_summary="List Tasks",
    tags=["Tasks"],
    manual_parameters=[
        openapi.Parameter(
            "status_id",
            openapi.IN_QUERY,
            description="Filter by status ID",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "user_id",
            openapi.IN_QUERY,
            description=(
                "Filter by user ID (only works if you have permission to view other users' tasks)"
            ),
            type=openapi.TYPE_NUMBER,
            required=False,
        ),
        openapi.Parameter(
            "created_at__gte",
            openapi.IN_QUERY,
            description="Filter by creation date greater than or equal (ISO 8601 format)",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            required=False,
        ),
        openapi.Parameter(
            "created_at__lte",
            openapi.IN_QUERY,
            description="Filter by creation date less than or equal (ISO 8601 format)",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            required=False,
        ),
        openapi.Parameter(
            "updated_at__gte",
            openapi.IN_QUERY,
            description="Filter by update date greater than or equal (ISO 8601 format)",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            required=False,
        ),
        openapi.Parameter(
            "updated_at__lte",
            openapi.IN_QUERY,
            description="Filter by update date less than or equal (ISO 8601 format)",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            required=False,
        ),
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number for pagination",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "page_size",
            openapi.IN_QUERY,
            description="Number of items per page (default: 20, max: 100)",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
    ],
    responses={
        200: openapi.Response(
            description="List of tasks",
            schema=PaginatedTaskSerializer,
        ),
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_tasks(request: Request) -> Response:
    try:
        queryset = get_task_queryset(request.user)

        filterset = TaskFilter(request.GET, queryset=queryset)
        queryset = filterset.qs

        page_obj = _pagination.badgerdoc_form_pagination(request, queryset)

        serializer = TaskSerializer(page_obj, many=True)

        next_url, previous_url = _pagination.badgerdoc_paginate(
            request, page_obj
        )

        return Response(
            {
                "count": page_obj.paginator.count,
                "next": next_url,
                "previous": previous_url,
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.exception("Failed to list tasks")
        return Response(
            {"error": f"Failed to list tasks: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description=(
        "Retrieve full task details including status, document metadata, tags, and related extractions."
    ),
    operation_summary="Retrieve Task Details",
    tags=["Tasks"],
    responses={
        200: openapi.Response(
            description="Successfully retrieved task details",
            schema=TaskSerializer,
        ),
        404: "Not Found - Task not found",
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_task_by_id(request: Request, task_id: int) -> Response:
    try:
        queryset = get_task_queryset(request.user)
        task_obj = queryset.get(id=task_id)

        serializer = TaskSerializer(task_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except task.Task.DoesNotExist:
        return Response(
            {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.exception("Failed to retrieve task details")
        return Response(
            {"error": f"Failed to retrieve task details: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
