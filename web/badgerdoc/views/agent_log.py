import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from badgerdoc import permissions
from badgerdoc.models import agent_log, document

logger = logging.getLogger(__name__)


class AgentLogPagination(PageNumberPagination):
    page_size = 20


class LogPayloadSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True)
    markdown = serializers.CharField(required=False, allow_blank=True)
    code = serializers.CharField(required=False, allow_blank=True)
    document = serializers.IntegerField(required=False, allow_null=True)
    workflow_params = serializers.JSONField(required=False, allow_null=True)

    def to_internal_value(self, data):
        allowed = {
            "message",
            "markdown",
            "code",
            "document",
            "workflow_params",
        }
        unknown = set(data) - allowed
        if unknown:
            raise serializers.ValidationError(
                f"Unknown field(s): {', '.join(sorted(unknown))}. "
                f"Allowed fields: {', '.join(sorted(allowed))}."
            )
        return super().to_internal_value(data)


class AgentLogSerializer(serializers.ModelSerializer):
    log = LogPayloadSerializer()

    class Meta:
        model = agent_log.AgentLog
        fields = (
            "id",
            "document",
            "task",
            "level",
            "source",
            "log",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class AgentLogView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List Agent Logs",
        operation_description=(
            "Returns logs for a document and all its descendants, ordered by `created_at` descending. "
            "Supports cursor-style polling via the `after` parameter."
        ),
        tags=["Agent"],
        manual_parameters=[
            openapi.Parameter(
                "document_id",
                openapi.IN_QUERY,
                description="ID of the document to fetch logs for (includes all descendant documents).",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "after",
                openapi.IN_QUERY,
                description="ISO 8601 datetime. Only logs with created_at >= this value are returned. Use for polling diffs.",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number (1-based, default 1).",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                description="Paginated list of agent logs.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "count": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "next": openapi.Schema(type=openapi.TYPE_STRING),
                        "previous": openapi.Schema(type=openapi.TYPE_STRING),
                        "results": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                        ),
                    },
                ),
            ),
            400: "Bad Request - Missing or invalid parameters",
            404: "Document not found",
        },
    )
    def get(self, request: Request) -> Response:
        document_id = request.query_params.get("document_id")
        if not document_id:
            return Response(
                {"error": "document_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        doc_qs = document.Document.objects.all()
        if not permissions.can_view_other_users_document(request.user):
            doc_qs = doc_qs.filter(uploaded_by=request.user)
        doc = get_object_or_404(doc_qs, id=document_id)

        path_prefix = agent_log.build_document_path(doc.id)

        qs = (
            agent_log.AgentLog.objects.filter(path__startswith=path_prefix)
            .defer("path")
            .order_by("-created_at")
        )

        after = request.query_params.get("after")
        if after:
            after_dt = parse_datetime(after)
            if after_dt is None:
                return Response(
                    {
                        "error": "Invalid 'after' value. Expected ISO 8601 datetime."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not timezone.is_aware(after_dt):
                after_dt = timezone.make_aware(after_dt)
            qs = qs.filter(created_at__gte=after_dt)

        paginator = AgentLogPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = AgentLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Create Agent Log",
        operation_description="Write a structured log entry for a document. Requires staff or `can_write_log` permission.",
        tags=["Agent"],
        request_body=AgentLogSerializer,
        responses={
            201: openapi.Response(
                description="Log entry created successfully",
                schema=AgentLogSerializer,
            ),
            400: "Bad Request - Invalid data",
            403: "Forbidden - Insufficient permissions",
            500: "Internal Server Error",
        },
    )
    def post(self, request: Request) -> Response:
        if not permissions.can_write_log(request.user):
            return Response(
                {"error": "You do not have permission to write logs."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            serializer = AgentLogSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            logger.exception("Validation error creating agent log")
            return Response(
                {"error": f"Validation error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            logger.exception("Failed to create agent log")
            return Response(
                {"error": "Failed to create agent log."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
