import logging

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from badgerdoc.models import tag

logger = logging.getLogger(__name__)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = tag.Tag
        fields = ["tag", "literal", "order"]
        read_only_fields = fields


@swagger_auto_schema(
    method="get",
    operation_description="List all tags, sorted by order.",
    operation_summary="List all tags",
    tags=["Tags"],
    responses={
        200: openapi.Response(
            description="List of all tags, ordered by priority",
            schema=TagSerializer(many=True),
        ),
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_tags(_: Request) -> Response:
    try:
        statuses = tag.Tag.objects.all().order_by("order")
        serializer = TagSerializer(statuses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Failed to list tags")
        return Response(
            {"error": f"Failed to list tags: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
