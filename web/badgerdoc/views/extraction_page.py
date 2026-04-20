import logging
from typing import Any

import django_filters
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from hocr_spec import HocrSpec, HocrValidator
from lxml import etree
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from badgerdoc import permissions
from badgerdoc.models import document, extraction, extraction_page
from badgerdoc.views import _pagination
from badgerdoc.views.extraction import (
    ExtractionFilter,
    get_extraction_queryset,
)

logger = logging.getLogger(__name__)


class ExtractionPageFilter(django_filters.FilterSet):
    extraction_id = django_filters.NumberFilter(field_name="extraction_id")
    page_number = django_filters.NumberFilter(field_name="page_number")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = extraction_page.ExtractionPage
        fields = ["extraction_id", "page_number"]


class ExtractionPageSerializer(serializers.ModelSerializer):
    extraction_id = serializers.PrimaryKeyRelatedField(
        source="extraction", queryset=extraction.Extraction.objects.all()
    )

    class Meta:
        model = extraction_page.ExtractionPage
        fields = [
            "id",
            "extraction_id",
            "page_number",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_page_number(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("Page number must be positive")
        return value


def validate_probable_hocr(content: str):
    if "XHTML" not in content and not content.startswith("<?xml"):
        try:
            etree.HTML(content.encode("utf-8"))
        except Exception as err:
            raise ValueError("Invalid HTML") from err
    else:
        report = HocrValidator.Report("extraction-page")
        HocrSpec().check(
            report,
            etree.HTML(content.encode("utf-8")),
        )

        if not report.is_valid():
            raise ValueError(report.format("text"))


class CreateExtractionPageSerializer(serializers.ModelSerializer):
    extraction_id = serializers.PrimaryKeyRelatedField(
        source="extraction", queryset=extraction.Extraction.objects.all()
    )

    class Meta:
        model = extraction_page.ExtractionPage
        fields = ["extraction_id", "page_number", "content"]

    def validate(self, attrs: dict) -> dict:
        request = self.context.get("request")
        extraction_: extraction.Extraction = attrs["extraction"]

        if request and extraction_.created_by != request.user:
            raise PermissionDenied(
                "Only the extraction creator can create pages for this extraction"
            )

        if not extraction_.is_in_progress():
            raise serializers.ValidationError(
                "Extraction has been stopped, no new modifications are allowed."
            )

        try:
            validate_probable_hocr(attrs["content"])
        except ValueError as e:
            raise serializers.ValidationError(
                f"Extraction page HTML content does not align with hOCR spec: {e}"
            )

        return attrs


class UpdateExtractionPageSerializer(serializers.Serializer):
    extraction_id = serializers.PrimaryKeyRelatedField(
        source="extraction",
        queryset=extraction.Extraction.objects.all(),
    )
    page_number = serializers.IntegerField(required=True)
    content = serializers.JSONField()

    def validate(self, attrs) -> dict:
        extraction_obj: extraction.Extraction = attrs.get("extraction")

        if not extraction_obj.is_in_progress():
            raise serializers.ValidationError(
                "Extraction has been stopped, no new modifications are allowed."
            )

        page_number = attrs.get("page_number")
        page_exists = extraction_page.ExtractionPage.objects.filter(
            extraction=extraction_obj, page_number=page_number
        ).exists()

        if not page_exists:
            raise serializers.ValidationError(
                f"Extraction page number {page_number} not found"
            )

        try:
            validate_probable_hocr(attrs["content"])
        except ValueError as e:
            raise serializers.ValidationError(
                f"Extraction page HTML content does not align with hOCR spec: {e}"
            )

        return attrs


PaginatedExtractionPageSerializer = _pagination.build_paginated_serializer(
    ExtractionPageSerializer
)


class ExtractionPageView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a new extraction page for an extraction",
        operation_summary="Create Extraction Page",
        tags=["Extraction Page"],
        request_body=ExtractionPageSerializer,
        responses={
            201: openapi.Response(
                description="Extraction page created successfully",
                schema=ExtractionPageSerializer,
            ),
            400: "Bad Request - Invalid data or extraction not found",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Only the extraction creator can create pages for this extraction",
            500: "Internal Server Error - Failed to create extraction page",
        },
    )
    def post(self, request: Request) -> Response:
        try:
            serializer = CreateExtractionPageSerializer(
                data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            page_obj = serializer.save()

            return Response(
                ExtractionPageSerializer(page_obj).data,
                status=status.HTTP_201_CREATED,
            )
        except PermissionDenied:
            raise
        except serializers.ValidationError as e:
            logger.exception("Validation error creating extraction page")
            return Response(
                {"error": f"Validation error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception("Failed to create extraction page")
            return Response(
                {"error": f"Failed to create extraction page: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Update extraction page content",
        operation_summary="Update Extraction Page",
        tags=["Extraction Page"],
        request_body=ExtractionPageSerializer,
        responses={
            200: openapi.Response(
                description="Extraction page updated successfully",
                schema=ExtractionPageSerializer,
            ),
            400: "Bad Request - Invalid data or extraction not found",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Only the extraction creator can create pages for this extraction",
            500: "Internal Server Error - Failed to create extraction page",
        },
    )
    def patch(self, request: Request) -> Response:
        try:
            serializer = UpdateExtractionPageSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            extraction_page_ = extraction_page.ExtractionPage.objects.filter(
                extraction_id=serializer.validated_data["extraction"].id,
                page_number=serializer.validated_data["page_number"],
            ).get()
            extraction_page_.content = serializer.validated_data["content"]
            extraction_page_.save()

            return Response(
                ExtractionPageSerializer(extraction_page_).data,
                status=status.HTTP_200_OK,
            )
        except PermissionDenied:
            raise
        except serializers.ValidationError as e:
            logger.exception("Validation error updating extraction page")
            return Response(
                {"error": f"Validation error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception("Failed to update extraction page")
            return Response(
                {"error": f"Failed to update extraction page: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def get_extraction_page_queryset(user: Any) -> Any:
    """Get queryset filtered by user permissions."""
    queryset = extraction_page.ExtractionPage.objects.select_related(
        "extraction", "extraction__created_by"
    ).all()

    if not permissions.can_view_other_users_extractions(user):
        queryset = queryset.filter(extraction__created_by=user)

    return queryset


@swagger_auto_schema(
    method="get",
    operation_description=(
        "List extraction pages with filtering. By default, users can only see pages from their own extractions. "
        "Staff users can see all extraction pages."
    ),
    operation_summary="List Extraction Pages",
    tags=["Extraction Page"],
    manual_parameters=[
        openapi.Parameter(
            "extraction_id",
            openapi.IN_QUERY,
            description="Filter by extraction ID",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "page_number",
            openapi.IN_QUERY,
            description="Filter by page number",
            type=openapi.TYPE_INTEGER,
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
            description="List of extraction pages",
            schema=PaginatedExtractionPageSerializer,
        ),
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_extraction_pages(request: Request) -> Response:
    try:
        queryset = get_extraction_page_queryset(request.user)

        filterset = ExtractionPageFilter(request.GET, queryset=queryset)
        queryset = filterset.qs

        page_obj = _pagination.badgerdoc_form_pagination(request, queryset)

        serializer = ExtractionPageSerializer(page_obj, many=True)

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
        logger.exception("Failed to list extraction pages")
        return Response(
            {"error": f"Failed to list extraction pages: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description=(
        "Get the latest extraction pages for a document. "
        "For each page number, returns the most recently created page across all extractions for this document."
    ),
    operation_summary="Get Latest Extraction Pages for Document",
    tags=["Document"],
    manual_parameters=[
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
        openapi.Parameter(
            "status",
            openapi.IN_QUERY,
            description="Filter by extraction status (case-insensitive exact match)",
            type=openapi.TYPE_STRING,
            required=False,
            enum=[value for (_, value) in extraction.ExtractionStatus.choices],
        ),
        openapi.Parameter(
            "created_by",
            openapi.IN_QUERY,
            description="Filter by extraction creator user ID",
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
            "tags",
            openapi.IN_QUERY,
            description=(
                "Filter by tags (comma-separated). Returns extractions that contain any of the specified tags."
            ),
            type=openapi.TYPE_STRING,
            required=False,
        ),
    ],
    responses={
        200: openapi.Response(
            description="Latest extraction pages retrieved successfully",
            schema=PaginatedExtractionPageSerializer,
        ),
        403: "Forbidden - No read permission",
        404: "Not Found - Document does not exist",
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_latest_extraction_pages(
    request: Request, document_id: int
) -> Response:
    logger.debug("Function called with document_id: %s", document_id)
    doc = get_object_or_404(document.Document, id=document_id)

    if not (
        request.user == doc.uploaded_by
        or permissions.can_view_other_users_document(request.user)
    ):
        return Response(
            {"error": "Permission denied. You must be the owner or admin."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        extraction_queryset = get_extraction_queryset(request.user).filter(
            document=doc
        )

        status_value = request.GET.get(
            "status", extraction.ExtractionStatus.COMPLETED
        )
        extraction_queryset = extraction_queryset.filter(status=status_value)

        filterset = ExtractionFilter(request.GET, queryset=extraction_queryset)
        filtered_extractions = filterset.qs

        extraction_ids = list(
            filtered_extractions.values_list("id", flat=True)
        )

        logger.info("Extraction ids: %s", extraction_ids)

        if not extraction_ids:
            return Response(
                {"count": 0, "next": None, "previous": None, "results": []},
                status=status.HTTP_200_OK,
            )

        all_pages = extraction_page.ExtractionPage.objects.filter(
            extraction_id__in=extraction_ids
        ).select_related("extraction", "extraction__document")

        latest_created_at_by_page = (
            all_pages.values("page_number")
            .annotate(latest_created_at=Max("created_at"))
            .values_list("page_number", "latest_created_at")
        )

        latest_page_filters = Q()
        for page_number, latest_created_at in latest_created_at_by_page:
            latest_page_filters |= Q(
                page_number=page_number, created_at=latest_created_at
            )

        latest_pages = all_pages.filter(latest_page_filters).order_by(
            "page_number"
        )

        page_obj = _pagination.badgerdoc_form_pagination(request, latest_pages)

        serializer = ExtractionPageSerializer(page_obj, many=True)

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
        logger.exception("Failed to get latest extraction pages")
        return Response(
            {"error": f"Failed to get latest extraction pages: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description="Get latest extraction page for specific page number by document ID with optional filters",
    operation_summary="Get Latest Extraction Page",
    tags=["Document"],
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
            description="Filter by user ID who created the extraction",
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
            description=(
                "Filter by tags (comma-separated). Returns extractions that contain any of the specified tags."
            ),
            type=openapi.TYPE_STRING,
            required=False,
        ),
    ],
    responses={
        200: openapi.Response(
            description="Latest extraction page retrieved successfully",
            schema=ExtractionPageSerializer,
        ),
        403: "Forbidden - No read permission",
        404: "Not Found - Document or extraction page does not exist",
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_latest_extraction_page(
    request: Request, document_id: int, page_num: int
) -> Response:
    doc = get_object_or_404(document.Document, id=document_id)

    if not (
        request.user == doc.uploaded_by
        or permissions.can_view_other_users_document(request.user)
    ):
        return Response(
            {"error": "Permission denied. You must be the owner or admin."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        extraction_queryset = get_extraction_queryset(request.user).filter(
            document=doc
        )

        status_value = request.GET.get(
            "status", extraction.ExtractionStatus.COMPLETED
        )
        extraction_queryset = extraction_queryset.filter(status=status_value)

        filterset = ExtractionFilter(request.GET, queryset=extraction_queryset)
        filtered_extractions = filterset.qs

        extraction_ids = list(
            filtered_extractions.values_list("id", flat=True)
        )

        if not extraction_ids:
            return Response(
                {
                    "error": f"No extraction found with the specified filters for document {document_id}"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        latest_page = (
            extraction_page.ExtractionPage.objects.filter(
                extraction_id__in=extraction_ids,
                page_number=page_num,
            )
            .select_related("extraction", "extraction__document")
            .order_by("-created_at")
            .first()
        )

        if not latest_page:
            return Response(
                {
                    "error": f"No extraction page found for page number {page_num}"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ExtractionPageSerializer(latest_page)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("Failed to get latest extraction page")
        return Response(
            {"error": f"Failed to get latest extraction page: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
