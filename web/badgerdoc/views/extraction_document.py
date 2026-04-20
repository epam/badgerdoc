import logging
from typing import cast

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from badgerdoc import permissions
from badgerdoc.models import extraction, extraction_document

logger = logging.getLogger(__name__)


class ExtractionDocumentSerializer(serializers.ModelSerializer):
    extraction_id = serializers.PrimaryKeyRelatedField(
        source="extraction", queryset=extraction.Extraction.objects.all()
    )

    class Meta:
        model = extraction_document.ExtractionDocument
        fields = [
            "id",
            "extraction_id",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CreateExtractionDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = extraction_document.ExtractionDocument
        fields = ["content"]


class ExtractionDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a new extraction document for an extraction",
        operation_summary="Create Extraction Document",
        tags=["Extraction Document"],
        manual_parameters=[
            openapi.Parameter(
                "extraction_id",
                openapi.IN_PATH,
                description="ID of the related extraction",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=CreateExtractionDocumentSerializer,
        responses={
            201: openapi.Response(
                description="Extraction document created successfully",
                schema=ExtractionDocumentSerializer,
            ),
            400: "Bad Request - Invalid data or extraction not found or not editable",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Only the extraction creator can create pages for this extraction",
            500: "Internal Server Error - Failed to create extraction document",
        },
    )
    def post(self, request: Request, extraction_id: int) -> Response:
        try:
            extraction_ = extraction.Extraction.objects.prefetch_related(
                "extraction_document"
            ).get(id=extraction_id)

            if extraction_.created_by != request.user:
                return Response(
                    {
                        "error": "Only the extraction creator can create a document for this extraction"
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if not extraction_.is_in_progress():
                return Response(
                    {
                        "error": "Extraction has been stopped, no new modifications are allowed."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if getattr(extraction_, "extraction_document", None):
                return Response(
                    {"error": "Extraction document already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data = dict(cast(dict, request.data))
            data["extraction_id"] = extraction_id

            serializer = ExtractionDocumentSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except extraction.Extraction.DoesNotExist:
            return Response(
                {"error": "Extraction not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except serializers.ValidationError as e:
            logger.exception("Validation error creating extraction document")
            return Response(
                {"error": f"Validation error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception("Failed to create extraction document")
            return Response(
                {"error": f"Failed to create extraction document: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Update extraction document for an extraction",
        operation_summary="Update Extraction Document",
        tags=["Extraction Document"],
        manual_parameters=[
            openapi.Parameter(
                "extraction_id",
                openapi.IN_PATH,
                description="ID of the extraction to update the document for",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=CreateExtractionDocumentSerializer,
        responses={
            200: openapi.Response(
                description="Extraction document updated successfully",
                schema=ExtractionDocumentSerializer,
            ),
            400: "Bad Request - Invalid data or extraction not found or not editable",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Only the extraction creator can create pages for this extraction",
            404: "Not Found - Extraction or extraction document not found",
            500: "Internal Server Error - Failed to create extraction document",
        },
    )
    def patch(self, request: Request, extraction_id: int) -> Response:
        try:
            extraction_document_ = (
                extraction_document.ExtractionDocument.objects.select_related(
                    "extraction",
                    "extraction__created_by",
                )
                .filter(extraction_id=extraction_id)
                .get()
            )
        except extraction_document.ExtractionDocument.DoesNotExist:
            return Response(
                {"error": "Extraction document or extraction not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if extraction_document_.extraction.created_by != request.user:
                return Response(
                    {
                        "error": "Only the extraction creator can create a document for this extraction"
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if not extraction_document_.extraction.is_in_progress():
                return Response(
                    {
                        "error": "Extraction has been stopped, no new modifications are allowed."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = CreateExtractionDocumentSerializer(
                extraction_document_, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            updated = serializer.save()

            response_serializer = ExtractionDocumentSerializer(updated)
            return Response(
                response_serializer.data, status=status.HTTP_200_OK
            )
        except serializers.ValidationError as e:
            logger.exception("Validation error creating extraction document")
            return Response(
                {"error": f"Validation error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception("Failed to update extraction document")
            return Response(
                {"error": f"Failed to update extraction document: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description=(
            "List extraction documents with filtering. By default, users can only see pages from their own extractions. "
            "Staff users can see all extraction documents."
        ),
        operation_summary="List Extraction Documents",
        tags=["Extraction Document"],
        manual_parameters=[
            openapi.Parameter(
                "extraction_id",
                openapi.IN_PATH,
                description="Filter by extraction ID",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={
            200: ExtractionDocumentSerializer,
            401: "Unauthorized - Authentication required",
            404: "Not found",
        },
    )
    def get(self, request: Request, extraction_id) -> Response:
        try:
            extraction_document_ = (
                extraction_document.ExtractionDocument.objects.select_related(
                    "extraction"
                )
                .filter(extraction_id=extraction_id)
                .get()
            )
        except extraction_document.ExtractionDocument.DoesNotExist:
            return Response(
                {"error": "Extraction document or extraction not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if not (
                request.user == extraction_document_.extraction.created_by
                or permissions.can_view_other_users_extractions(request.user)
            ):
                return Response(
                    {
                        "error": "Permission denied. You must be the owner or admin."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = ExtractionDocumentSerializer(extraction_document_)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Failed to list extraction documents")
            return Response(
                {"error": f"Failed to list extraction documents: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
