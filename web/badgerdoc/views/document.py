import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import django_filters
from django.db.models import Q
from django.http import HttpResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from PIL import Image
from rest_framework import parsers, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from badgerdoc import chunk_xpath, permissions
from badgerdoc.models import document, extraction, extraction_page
from badgerdoc.views import _pagination

logger = logging.getLogger(__name__)


class DocumentFilter(django_filters.FilterSet):
    uploaded_by = django_filters.NumberFilter(field_name="uploaded_by")
    parent_document_id = django_filters.NumberFilter(
        method="filter_parent_document_id"
    )
    tags = django_filters.CharFilter(method="filter_tags")
    metadata = django_filters.CharFilter(method="filter_metadata")
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = document.Document
        fields = ["uploaded_by", "parent_document_id", "tags"]

    def filter_parent_document_id(
        self, queryset: Any, _name: str, value: str
    ) -> Any:
        try:
            return queryset.filter(parent_document=int(value))
        except (ValueError, TypeError):
            logger.exception("Invalid parent_id value")
            return queryset

    def filter_tags(self, queryset: Any, _name: str, value: str) -> Any:
        if not value:
            return queryset
        tag_list = [tag.strip() for tag in value.split(",")]
        q_objects = Q()
        for tag in tag_list:
            q_objects |= Q(tags__contains=[tag])
        return queryset.filter(q_objects)

    def filter_metadata(self, queryset: Any, _name: str, value: str) -> Any:
        if not value:
            return queryset

        try:
            filter_data = json.loads(value)
        except json.JSONDecodeError:
            return queryset

        overall_q = Q()
        for key, values in filter_data.items():
            key_q = Q()
            if isinstance(values, list):
                for item in values:
                    key_q |= Q(**{f"metadata__{key}": item})
            else:
                key_q = Q(**{f"metadata__{key}": values})

            overall_q &= key_q

        return queryset.filter(overall_q)


class DocumentChangeSerializer(serializers.ModelSerializer):
    parent_document_id = serializers.PrimaryKeyRelatedField(
        source="parent_document",
        queryset=document.Document.objects.all(),
        required=False,
        allow_null=True,
    )
    metadata = serializers.JSONField(required=False, allow_null=True)
    tags = serializers.JSONField(required=False, allow_null=True)
    extension = serializers.CharField(
        required=False, allow_blank=True, max_length=8
    )

    class Meta:
        model = document.Document
        ref_name = "document.DocumentCreateUpdateSerializer"
        fields = [
            "parent_document_id",
            "metadata",
            "tags",
            "file",
            "extension",
        ]

    def create(self, validated_data: dict[str, Any]) -> document.Document:
        validated_data["uploaded_by"] = self.context["request"].user
        return super().create(validated_data)

    def validate_parent_document_id(
        self, value: document.Document | None
    ) -> document.Document | None:
        if value is None:
            return value
        request = self.context.get("request")
        if request and value.uploaded_by != request.user:
            raise serializers.ValidationError(
                "You can only set a parent document that you own."
            )
        return value

    def validate_metadata(
        self, value: str | dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError as err:
                raise serializers.ValidationError(
                    "Invalid JSON format in metadata field"
                ) from err
        return value

    def validate_tags(self, value: list[str] | str | None) -> list[str] | None:
        if value is None:
            return value
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list")
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("All tags must be strings")
        return value


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)
    parent_document_id = serializers.PrimaryKeyRelatedField(
        source="parent_document",
        read_only=True,
    )

    class Meta:
        model = document.Document
        ref_name = "document.DocumentSerializer"
        fields = [
            "id",
            "uploaded_by",
            "parent_document_id",
            "file",
            "extension",
            "metadata",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


PaginatedDocumentSerializer = _pagination.build_paginated_serializer(
    DocumentSerializer
)


def get_document_queryset(user: Any) -> Any:
    queryset = document.Document.objects.select_related("uploaded_by").all()

    if not permissions.can_view_other_users_document(user):
        queryset = queryset.filter(uploaded_by=user)

    return queryset


@swagger_auto_schema(
    method="get",
    operation_description=(
        "List documents with filtering. By default, users can only see their own documents. "
        "Staff users can see all documents. Filter by metadata fields using the 'metadata_filter' parameter with JSON."
    ),
    operation_summary="List Documents",
    tags=["Document"],
    manual_parameters=[
        openapi.Parameter(
            "uploaded_by",
            openapi.IN_QUERY,
            description=(
                "Filter by uploader user ID (only works if you have permission to view other users' documents)"
            ),
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "parent_document_id",
            openapi.IN_QUERY,
            description=(
                "Filter by parent document. If not provided, shows only documents without parent. "
                "If provided with integer ID, shows documents with that parent."
            ),
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "tags",
            openapi.IN_QUERY,
            description=(
                "Filter by tags (comma-separated list). Returns documents containing at least one of the specified tags"
            ),
            type=openapi.TYPE_STRING,
            required=False,
        ),
        openapi.Parameter(
            "created_at__gte",
            openapi.IN_QUERY,
            description=(
                "Filter by creation date greater than or equal (ISO 8601 format)"
            ),
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            required=False,
        ),
        openapi.Parameter(
            "created_at__lte",
            openapi.IN_QUERY,
            description=(
                "Filter by creation date less than or equal (ISO 8601 format)"
            ),
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
        openapi.Parameter(
            "metadata",
            openapi.IN_QUERY,
            description=(
                "Filter by metadata fields in a OR-based notation. "
                'Example: {"external_id": ["id1", "id2", "id3"], authors__contains: ["author1"]}.'
            ),
            type=openapi.TYPE_STRING,
            required=False,
        ),
    ],
    responses={
        200: openapi.Response(
            description="List of documents",
            schema=PaginatedDocumentSerializer,
        ),
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_documents(request: Request) -> Response:
    try:
        queryset = get_document_queryset(request.user)

        # Apply default parent_document_id filter if not specified
        if "parent_document_id" not in request.GET:
            queryset = queryset.filter(parent_document__isnull=True)

        filterset = DocumentFilter(request.GET, queryset=queryset)
        queryset = filterset.qs

        page_obj = _pagination.badgerdoc_form_pagination(request, queryset)

        serializer = DocumentSerializer(page_obj, many=True)

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
        logger.exception("Failed to list documents")
        return Response(
            {"error": f"Failed to list documents: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _parse_form_request_data(request: Request) -> dict[str, Any]:
    document_data = {}
    document_data["file"] = (request.FILES or {}).get("file")
    document_data["metadata"] = request.data.get("metadata", {})
    document_data["parent_document_id"] = request.data.get(
        "parent_document_id", None
    )
    document_data["extension"] = request.data.get("extension", None)

    tags = request.data.get("tags", None)

    if tags and isinstance(tags, str):
        document_data["tags"] = json.loads(tags)

    return {
        key: value for key, value in document_data.items() if value is not None
    }


def _create_rendition_from_png(document_obj: document.Document) -> None:
    # Creates a rendition only from PNG uploads. For other file types (PDF, etc.),
    # renditions are produced by the Convert workflows (see workflows/badgerdoc_convert).
    if document_obj.parent_document is not None:
        return
    if document_obj.tags and "rendition" in document_obj.tags:
        return
    ext = (document_obj.extension or "").lower()
    if ext != "png":
        return
    with document_obj.file.open("rb") as f:
        image = Image.open(f)
        image.load()
        width, height = image.size
    document.Document.objects.create(
        file=document_obj.file,
        name=document_obj.name,
        extension=document_obj.extension,
        uploaded_by=document_obj.uploaded_by,
        parent_document=document_obj,
        tags=["rendition"],
        metadata={"page": 1, "size": {"width": width, "height": height}},
    )


@swagger_auto_schema(
    method="post",
    operation_description="Create document and optionally upload a file",
    operation_summary="Create Document",
    tags=["Document"],
    request_body=DocumentChangeSerializer,
    consumes=["multipart/form-data"],
    responses={
        201: openapi.Response(
            description="Document uploaded successfully",
            schema=DocumentSerializer,
        ),
        400: "Bad Request - No file provided or invalid file",
        401: "Unauthorized - Authentication required",
        500: "Internal Server Error - Failed to upload document",
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_document(request: Request) -> Response:
    try:
        document_data = _parse_form_request_data(request)
    except json.JSONDecodeError as err:
        return Response(
            {"error": f"Invalid JSON format received: {err}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        serializer = DocumentChangeSerializer(
            data=document_data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        document_obj = serializer.save()
        _create_rendition_from_png(document_obj)

        return Response(
            DocumentSerializer(document_obj).data,
            status=status.HTTP_201_CREATED,
        )
    except serializers.ValidationError:
        raise
    except Exception as e:
        logger.exception("Failed to upload document")
        return Response(
            {"error": f"Failed to upload document: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description="Get document renditions by parent document ID. Returns child documents with 'rendition' tag.",
    operation_summary="Get Document Renditions",
    tags=["Document"],
    manual_parameters=[
        openapi.Parameter(
            "document_id",
            openapi.IN_PATH,
            description="ID of the parent document",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            description="List of document renditions",
            schema=serializers.ListSerializer(child=DocumentSerializer()),
        ),
        404: "Not Found - Parent document does not exist",
        401: "Unauthorized - Authentication required",
        403: "Forbidden - No permission to view this document",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_document_renditions(request: Request, document_id: int) -> Response:
    try:
        document_ = (
            get_document_queryset(request.user).filter(id=document_id).first()
        )
        if document_ is None:
            return Response(
                {"error": f"Document with id {document_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        renditions = (
            document.Document.objects.select_related("uploaded_by")
            .filter(parent_document=document_id)
            .filter(tags__contains=["rendition"])
        )

        serializer = DocumentSerializer(renditions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("Failed to get document renditions")
        return Response(
            {"error": f"Failed to get document renditions: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description="Get rendition document for a specific page of a parent document.",
    operation_summary="Get Document Rendition Page",
    tags=["Document"],
    manual_parameters=[
        openapi.Parameter(
            "document_id",
            openapi.IN_PATH,
            description="ID of the parent document",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "page",
            openapi.IN_PATH,
            description="Page number of the rendition",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            description="Rendition document for the requested page",
            schema=DocumentSerializer(),
        ),
        404: "Not Found - Document or rendition page not found",
        401: "Unauthorized - Authentication required",
        403: "Forbidden - No permission to view this document",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_document_rendition_page(
    request: Request, document_id: int, page: int
) -> Response:
    try:
        document_ = (
            get_document_queryset(request.user).filter(id=document_id).first()
        )
        if document_ is None:
            return Response(
                {"error": f"Document with id {document_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        rendition = _find_rendition_by_page(document_id, page)
        if rendition is None:
            return Response(
                {"error": f"Rendition for page {page} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DocumentSerializer(rendition)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("Failed to get document rendition page")
        return Response(
            {"error": f"Failed to get document rendition page: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _find_rendition_by_page(document_id: int, page: int):
    """Find rendition document by document_id and page number"""
    renditions = document.Document.objects.filter(
        parent_document=document_id
    ).filter(tags__contains=["rendition"])

    for rend in renditions:
        if rend.metadata and rend.metadata.get("page") == page:
            return rend
    return None


@swagger_auto_schema(
    method="get",
    operation_description="Get DZI documents for a parent document. Returns documents with ['dzi', 'xml'] tags that are children of renditions of the specified document.",
    operation_summary="Get Document DZI Files",
    tags=["Document"],
    manual_parameters=[
        openapi.Parameter(
            "document_id",
            openapi.IN_PATH,
            description="ID of the parent document",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            description="List of DZI URLs",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
            ),
        ),
        404: "Not Found - Parent document does not exist",
        401: "Unauthorized - Authentication required",
        403: "Forbidden - No permission to view this document",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_document_dzi(request: Request, document_id: int) -> Response:
    try:
        document_ = (
            get_document_queryset(request.user).filter(id=document_id).first()
        )
        if document_ is None:
            return Response(
                {"error": f"Document with id {document_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        renditions = (
            document.Document.objects.filter(parent_document=document_id)
            .filter(tags__contains=["rendition"])
            .values_list("id", flat=True)
        )

        dzi_documents = (
            document.Document.objects.select_related("uploaded_by")
            .filter(parent_document__in=renditions)
            .filter(tags__contains=["dzi"])
            .filter(tags__contains=["xml"])
        )

        dzi_documents = sorted(
            dzi_documents,
            key=lambda doc: doc.metadata.get("page", 0) if doc.metadata else 0,
        )

        dzi_urls = []
        for dzi_doc in dzi_documents:
            if not dzi_doc.metadata or not dzi_doc.metadata.get("page"):
                logger.warning(
                    "DZI document %s has no page metadata, skipping",
                    dzi_doc.id,
                )
                continue

            page = dzi_doc.metadata.get("page")
            document_name = document_.name or f"document_{document_id}"
            dzi_url = f"/badgerdoc/document/{document_id}/dzi/page/{page}/{document_name}/{document_name}.dzi"
            dzi_urls.append(dzi_url)

        return Response(dzi_urls, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("Failed to get document DZI files")
        return Response(
            {"error": f"Failed to get document DZI files: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description="Get DZI XML content for a specific page of a document.",
    operation_summary="Get DZI XML Content",
    tags=["Document"],
    manual_parameters=[
        openapi.Parameter(
            "document_id",
            openapi.IN_PATH,
            description="ID of the parent document",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "page",
            openapi.IN_PATH,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "name",
            openapi.IN_PATH,
            description="Document name",
            type=openapi.TYPE_STRING,
            required=True,
        ),
        openapi.Parameter(
            "dzi_name",
            openapi.IN_PATH,
            description="DZI filename",
            type=openapi.TYPE_STRING,
            required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            description="DZI XML content",
            schema=openapi.Schema(type=openapi.TYPE_STRING),
        ),
        404: "Not Found - DZI document not found",
        401: "Unauthorized - Authentication required",
        500: "Internal Server Error - Failed to retrieve DZI content",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_document_dzi_content(
    request: Request,
    document_id: int,
    page: int,
    name: str,  # pylint: disable=unused-argument
    dzi_name: str,  # pylint: disable=unused-argument
) -> HttpResponse:
    try:
        rendition = _find_rendition_by_page(document_id, page)
        if not rendition:
            return HttpResponse(
                "Rendition not found for specified page",
                status=404,
                content_type="text/plain",
            )

        dzi_document = (
            document.Document.objects.filter(parent_document=rendition.id)
            .filter(tags__contains=["dzi"])
            .filter(tags__contains=["xml"])
            .first()
        )

        if not dzi_document:
            return HttpResponse(
                "DZI document not found", status=404, content_type="text/plain"
            )

        if not dzi_document.file:
            return HttpResponse(
                "DZI file not found", status=404, content_type="text/plain"
            )

        file_url = dzi_document.file.url
        if file_url.startswith("/"):
            file_url = request.build_absolute_uri(file_url)

        with urllib.request.urlopen(file_url) as response:  # nosec B310
            content = response.read()

        return HttpResponse(content, content_type="application/xml")

    except urllib.error.URLError as e:
        logger.exception("Failed to fetch DZI file from storage")
        return HttpResponse(
            f"Failed to fetch DZI file: {str(e)}",
            status=500,
            content_type="text/plain",
        )
    except Exception as e:
        logger.exception("Failed to get DZI content")
        return HttpResponse(
            f"Failed to get DZI content: {str(e)}",
            status=500,
            content_type="text/plain",
        )


@swagger_auto_schema(
    method="get",
    operation_description="Get DZI PNG tile content for a specific layer and position.",
    operation_summary="Get DZI PNG Tile",
    tags=["Document"],
    manual_parameters=[
        openapi.Parameter(
            "document_id",
            openapi.IN_PATH,
            description="ID of the parent document",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "page",
            openapi.IN_PATH,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "name",
            openapi.IN_PATH,
            description="Document name",
            type=openapi.TYPE_STRING,
            required=True,
        ),
        openapi.Parameter(
            "dzi_name",
            openapi.IN_PATH,
            description="DZI name",
            type=openapi.TYPE_STRING,
            required=True,
        ),
        openapi.Parameter(
            "layer",
            openapi.IN_PATH,
            description="Tile layer number",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "position",
            openapi.IN_PATH,
            description="Tile position (e.g. 1_2)",
            type=openapi.TYPE_STRING,
            required=True,
        ),
    ],
    responses={
        200: openapi.Response(
            description="PNG tile content",
            schema=openapi.Schema(
                type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY
            ),
        ),
        404: "Not Found - Tile not found",
        401: "Unauthorized - Authentication required",
        500: "Internal Server Error - Failed to retrieve tile",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_document_dzi_tile(
    request: Request,
    document_id: int,
    page: int,
    name: str,  # pylint: disable=unused-argument
    dzi_name: str,  # pylint: disable=unused-argument
    layer: int,
    position: str,
) -> HttpResponse:
    try:
        rendition = _find_rendition_by_page(document_id, page)
        if not rendition:
            return HttpResponse(
                "Rendition not found for specified page",
                status=404,
                content_type="text/plain",
            )

        tile_tag = f"{layer}/{position}.png"

        tile_document = (
            document.Document.objects.filter(parent_document=rendition.id)
            .filter(tags__contains=["dzi"])
            .filter(tags__contains=[tile_tag])
            .first()
        )

        if not tile_document:
            return HttpResponse(
                "Tile not found", status=404, content_type="text/plain"
            )

        if not tile_document.file:
            return HttpResponse(
                "Tile file not found", status=404, content_type="text/plain"
            )

        file_url = tile_document.file.url
        if file_url.startswith("/"):
            file_url = request.build_absolute_uri(file_url)

        with urllib.request.urlopen(file_url) as response:  # nosec B310
            content = response.read()

        return HttpResponse(content, content_type="image/png")

    except urllib.error.URLError as e:
        logger.exception("Failed to fetch tile from storage")
        return HttpResponse(
            f"Failed to fetch tile: {str(e)}",
            status=500,
            content_type="text/plain",
        )
    except Exception as e:
        logger.exception("Failed to get tile content")
        return HttpResponse(
            f"Failed to get tile content: {str(e)}",
            status=500,
            content_type="text/plain",
        )


@swagger_auto_schema(
    method="get",
    operation_summary="Get or Create Document Chunk",
    tags=["Document"],
    manual_parameters=[
        openapi.Parameter(
            "document_id",
            openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
        ),
        openapi.Parameter(
            "page_num",
            openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
        ),
        openapi.Parameter(
            "extraction_id",
            openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
        ),
        openapi.Parameter(
            "xpath",
            openapi.IN_PATH,
            type=openapi.TYPE_STRING,
        ),
    ],
    responses={
        200: openapi.Response(
            description="Chunk document",
            schema=DocumentSerializer,
        ),
        400: "Bad request",
        404: "Not found",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_document_chunk(
    request: Request,
    document_id: int,
    page_num: int,
    extraction_id: int,
    xpath: str,
) -> Response:
    try:
        xpath = urllib.parse.unquote(xpath)

        document_obj = (
            get_document_queryset(request.user).filter(id=document_id).first()
        )
        if not document_obj:
            return Response(
                {"detail": "Document not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            extraction_obj = extraction.Extraction.objects.get(
                id=extraction_id
            )
        except extraction.Extraction.DoesNotExist:
            return Response(
                {"detail": "Extraction not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if extraction_obj.document_id != document_id:
            return Response(
                {"detail": "Extraction does not belong to document"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            extraction_page_obj = extraction_page.ExtractionPage.objects.get(
                extraction_id=extraction_id,
                page_number=page_num,
            )
        except extraction_page.ExtractionPage.DoesNotExist:
            return Response(
                {"detail": "Extraction page not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            x1, y1, x2, y2 = chunk_xpath.extract_bbox_from_hocr(
                extraction_page_obj.content, xpath
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        coordinates_str = f"{x1} {y1} {x2} {y2}"

        existing_chunk = chunk_xpath.find_existing_chunk(
            document_id, page_num, coordinates_str
        )
        if existing_chunk:
            return Response(
                DocumentSerializer(existing_chunk).data,
                status=status.HTTP_200_OK,
            )

        rendition = _find_rendition_by_page(document_id, page_num)
        if not rendition:
            return Response(
                {"detail": "Rendition not found for page"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            png_bytes = chunk_xpath.crop_rendition(rendition, x1, y1, x2, y2)
        except chunk_xpath.RenditionMissingSizeError:
            return Response(
                {"detail": "rendition created without size"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        chunk_doc = chunk_xpath.create_chunk_document(
            document_obj, request.user, page_num, x1, y1, x2, y2, png_bytes
        )

        return Response(
            DocumentSerializer(chunk_doc).data, status=status.HTTP_200_OK
        )

    except Exception:
        logger.exception("Failed to get document chunk")
        return Response(
            {"detail": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class DocumentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    @swagger_auto_schema(
        operation_description="Get document details by ID",
        operation_summary="Get Document",
        tags=["Document"],
        responses={
            200: openapi.Response(
                description="Document details retrieved successfully",
                schema=DocumentSerializer,
            ),
            403: "Forbidden - No read permission",
            404: "Not Found - Document does not exist",
            401: "Unauthorized - Authentication required",
        },
    )
    def get(self, request: Request, document_id: int) -> Response:
        document_ = (
            get_document_queryset(request.user).filter(id=document_id).first()
        )
        if document_ is None:
            return Response(
                {"error": f"Document with id {document_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            DocumentSerializer(document_).data, status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description="Update a file or metadata for an existing document",
        operation_summary="Update Document",
        tags=["Document"],
        manual_parameters=[
            openapi.Parameter(
                "document_id",
                openapi.IN_PATH,
                description="ID of the document to update",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=DocumentChangeSerializer(partial=True),
        consumes=["multipart/form-data"],
        responses={
            200: DocumentSerializer,
            400: "Bad Request - No file provided",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
        },
    )
    def patch(self, request: Request, document_id: int) -> Response:
        document_ = (
            get_document_queryset(request.user).filter(id=document_id).first()
        )
        if document_ is None:
            return Response(
                {"error": f"Document with id {document_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            document_data = _parse_form_request_data(request)
        except json.JSONDecodeError as err:
            return Response(
                {"error": f"Invalid JSON format received: {err}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            serializer = DocumentChangeSerializer(
                document_,
                data=document_data,
                context={"request": request},
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            document_obj = serializer.save()

            return Response(
                DocumentSerializer(document_obj).data,
                status=status.HTTP_200_OK,
            )
        except serializers.ValidationError:
            raise
        except Exception as e:
            logger.exception("Failed to upload document")
            return Response(
                {"error": f"Failed to upload document: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Delete a document by ID. Can be done by document owner or staff users.",
        operation_summary="Delete Document",
        tags=["Document"],
        manual_parameters=[
            openapi.Parameter(
                "document_id",
                openapi.IN_PATH,
                description="ID of the document to delete",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            204: "No Content - Document deleted successfully",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - No delete permission",
            404: "Not Found - Document does not exist",
            500: "Internal Server Error - Failed to delete document",
        },
    )
    def delete(self, request: Request, document_id: int) -> Response:
        try:
            document_ = (
                get_document_queryset(request.user)
                .filter(id=document_id)
                .first()
            )
            if document_ is None:
                return Response(
                    {"error": f"Document with id {document_id} not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if (
                document_.uploaded_by != request.user
                and not permissions.can_delete_document(request.user)
            ):
                return Response(
                    {
                        "error": "You do not have permission to delete this document."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            document_.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.exception("Failed to delete document")
            return Response(
                {"error": f"Failed to delete document: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
