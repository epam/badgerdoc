import logging
from typing import Any

import django_filters
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from badgerdoc import permissions
from badgerdoc.models import document, extraction
from badgerdoc.views import _pagination

logger = logging.getLogger(__name__)


class ExtractionFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=extraction.ExtractionStatus.choices,
    )
    document_id = django_filters.NumberFilter(field_name="document_id")
    created_by = django_filters.NumberFilter(field_name="created_by")
    temporal_job_id = django_filters.CharFilter(lookup_expr="icontains")
    task_id = django_filters.NumberFilter(
        field_name="task_assignments__task_id"
    )
    tags = django_filters.CharFilter(method="filter_tags")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = extraction.Extraction
        fields = [
            "document_id",
            "created_by",
            "temporal_job_id",
            "task_id",
            "tags",
        ]

    # pylint: disable=unused-argument
    def filter_tags(self, queryset: Any, name: str, value: str) -> Any:
        if not value:
            return queryset
        tag_list = [tag.strip() for tag in value.split(",")]
        q_objects = Q()
        for tag in tag_list:
            q_objects |= Q(tags__contains=[tag])
        return queryset.filter(q_objects)


class ExtractionSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    document_id = serializers.PrimaryKeyRelatedField(
        source="document",
        read_only=True,
    )
    status = serializers.ChoiceField(
        choices=[value for (_, value) in extraction.ExtractionStatus.choices],
        read_only=True,
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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


PaginatedExtractionSerializer = _pagination.build_paginated_serializer(
    ExtractionSerializer
)


class CreateExtractionSerializer(serializers.ModelSerializer):
    document_id = serializers.PrimaryKeyRelatedField(
        source="document", queryset=document.Document.objects.all()
    )
    status = serializers.ChoiceField(
        choices=[value for (_, value) in extraction.ExtractionStatus.choices],
        required=False,
    )

    class Meta:
        model = extraction.Extraction
        fields = [
            "document_id",
            "status",
            "comment",
            "tags",
        ]

    def create(self, validated_data: dict[str, Any]) -> extraction.Extraction:
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class UpdateExtractionSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(
        choices=[value for (_, value) in extraction.ExtractionStatus.choices],
        required=False,
    )

    class Meta:
        model = extraction.Extraction
        fields = ["status", "comment", "tags"]


@swagger_auto_schema(
    method="post",
    operation_description="Create a new extraction for a document",
    operation_summary="Create Extraction",
    tags=["Extraction"],
    request_body=CreateExtractionSerializer(),
    responses={
        201: openapi.Response(
            description="Extraction created successfully",
            schema=ExtractionSerializer,
        ),
        400: "Bad Request - Invalid data or document not found",
        401: "Unauthorized - Authentication required",
        500: "Internal Server Error - Failed to create extraction",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_extraction(request: Request) -> Response:
    try:
        serializer = CreateExtractionSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        new_extraction = serializer.save()

        return Response(
            ExtractionSerializer(new_extraction).data,
            status=status.HTTP_201_CREATED,
        )

    except serializers.ValidationError as e:
        logger.exception("Validation error creating extraction")
        return Response(
            {"error": f"Validation error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception("Failed to create extraction")
        return Response(
            {"error": f"Failed to create extraction: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def get_extraction_queryset(user: Any) -> Any:
    """Get queryset filtered by user permissions."""
    queryset = extraction.Extraction.objects.select_related(
        "document", "created_by"
    ).all()

    if not permissions.can_view_other_users_extractions(user):
        queryset = queryset.filter(created_by=user)

    return queryset


@swagger_auto_schema(
    method="get",
    operation_description=(
        "List extractions with filtering. By default, users can only see their own extractions. "
        "Staff users can see all extractions."
    ),
    operation_summary="List Extractions",
    tags=["Extraction"],
    manual_parameters=[
        openapi.Parameter(
            "status",
            openapi.IN_QUERY,
            description="Filter by status (case-insensitive exact match)",
            type=openapi.TYPE_STRING,
            required=False,
            enum=[value for (_, value) in extraction.ExtractionStatus.choices],
        ),
        openapi.Parameter(
            "document_id",
            openapi.IN_QUERY,
            description="Filter by document ID",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "task_id",
            openapi.IN_QUERY,
            description="Filter by task ID",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "created_by",
            openapi.IN_QUERY,
            description=(
                "Filter by creator user ID (only works if you have permission to view other users' extractions)"
            ),
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "temporal_job_id",
            openapi.IN_QUERY,
            description="Filter by temporal job ID (case-insensitive contains)",
            type=openapi.TYPE_STRING,
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
            "tags",
            openapi.IN_QUERY,
            description="Filter by tags (comma-separated list). Returns extractions containing at least one of the specified tags",
            type=openapi.TYPE_STRING,
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
            description="List of extractions",
            schema=PaginatedExtractionSerializer,
        ),
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_extractions(request: Request) -> Response:
    try:
        queryset = get_extraction_queryset(request.user)

        filterset = ExtractionFilter(request.GET, queryset=queryset)
        queryset = filterset.qs

        page_obj = _pagination.badgerdoc_form_pagination(request, queryset)

        serializer = ExtractionSerializer(page_obj, many=True)

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
        logger.exception("Failed to list extractions")
        return Response(
            {"error": f"Failed to list extractions: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description="List all unique tags from extractions with filtering",
    operation_summary="List Extraction Tags",
    tags=["Extraction"],
    manual_parameters=[
        openapi.Parameter(
            "status",
            openapi.IN_QUERY,
            description="Filter by extraction status (defaults to 'Completed')",
            type=openapi.TYPE_STRING,
            required=False,
            enum=[value for (_, value) in extraction.ExtractionStatus.choices],
        ),
        openapi.Parameter(
            "created_by",
            openapi.IN_QUERY,
            description="Filter by creator user ID",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "temporal_job_id",
            openapi.IN_QUERY,
            description="Filter by temporal job ID (partial match)",
            type=openapi.TYPE_STRING,
            required=False,
        ),
        openapi.Parameter(
            "tags",
            openapi.IN_QUERY,
            description="Filter by tags (comma-separated). Returns extractions that contain any of the specified tags.",
            type=openapi.TYPE_STRING,
            required=False,
        ),
    ],
    responses={
        200: openapi.Response(
            description="List of unique tag names",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Tag name",
                ),
                description="Array of unique tag strings",
            ),
        ),
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_extraction_tags(request: Request) -> Response:
    try:
        queryset = get_extraction_queryset(request.user)

        status_value = request.GET.get(
            "status", extraction.ExtractionStatus.COMPLETED
        )
        queryset = queryset.filter(status=status_value)

        filterset = ExtractionFilter(request.GET, queryset=queryset)
        queryset = filterset.qs

        unique_tags = (
            queryset.extra(select={"tag": "jsonb_array_elements_text(tags)"})
            .values_list("tag", flat=True)
            .distinct()
            .order_by("tag")
        )

        return Response(list(unique_tags), status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("Failed to list extraction tags")
        return Response(
            {"error": f"Failed to list extraction tags: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ExtractionView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get extraction details by ID",
        operation_summary="Get Extraction",
        tags=["Extraction"],
        responses={
            200: openapi.Response(
                description="Extraction details retrieved successfully",
                schema=ExtractionSerializer,
            ),
            403: "Forbidden - No read permission",
            404: "Not Found - Extraction does not exist",
            401: "Unauthorized - Authentication required",
        },
    )
    def get(self, request: Request, extraction_id: int) -> Response:
        extraction_obj = get_object_or_404(
            extraction.Extraction, id=extraction_id
        )

        if not (
            request.user == extraction_obj.created_by
            or permissions.can_view_other_users_extractions(request.user)
        ):
            return Response(
                {
                    "error": "Permission denied. You must be the owner or admin."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ExtractionSerializer(extraction_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Update an existing extraction",
        operation_summary="Update Extraction",
        tags=["Extraction"],
        manual_parameters=[
            openapi.Parameter(
                "extraction_id",
                openapi.IN_PATH,
                description="ID of the extraction to update",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=UpdateExtractionSerializer(partial=True),
        responses={
            200: openapi.Response(
                description="Extraction updated successfully",
                schema=ExtractionSerializer,
            ),
            400: "Bad Request - Invalid data",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Only the extraction creator can update this extraction",
            404: "Not Found - Extraction not found",
            500: "Internal Server Error - Failed to update extraction",
        },
    )
    def patch(self, request: Request, extraction_id: int) -> Response:
        try:
            extraction_obj = extraction.Extraction.objects.get(
                pk=extraction_id
            )

            if extraction_obj.created_by != request.user:
                return Response(
                    {
                        "error": "Only the extraction creator can update this extraction"
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            update_serializer = UpdateExtractionSerializer(
                extraction_obj, data=request.data, partial=True
            )
            update_serializer.is_valid(raise_exception=True)
            updated_extraction = update_serializer.save()

            response_serializer = ExtractionSerializer(updated_extraction)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK,
            )

        except extraction.Extraction.DoesNotExist:
            return Response(
                {"error": "Extraction not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except serializers.ValidationError as e:
            logger.exception("Validation error updating extraction")
            return Response(
                {"error": f"Validation error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception("Failed to update extraction")
            return Response(
                {"error": f"Failed to update extraction: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
