import logging

from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from badgerdoc.models import task_status

logger = logging.getLogger(__name__)


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = task_status.TaskStatus
        fields = ["id", "name", "order"]
        read_only_fields = ["id"]


@swagger_auto_schema(
    method="get",
    operation_description="List all task statuses in the hierarchy, sorted by order.",
    operation_summary="List all task statuses",
    tags=["Tasks"],
    responses={
        200: openapi.Response(
            description="List of all task statuses, ordered by priority",
            schema=TaskStatusSerializer(many=True),
        ),
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
# pylint: disable=unused-argument
def list_task_statuses(
    request: Request,
) -> Response:
    try:
        statuses = task_status.TaskStatus.objects.all().order_by("order")
        serializer = TaskStatusSerializer(statuses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Failed to list task statuses")
        return Response(
            {"error": f"Failed to list task statuses: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@swagger_auto_schema(
    method="get",
    operation_description="List next possible task statuses for the given status ID, sorted by priority.",
    operation_summary="List next task statuses",
    tags=["Tasks"],
    manual_parameters=[
        openapi.Parameter(
            "current_status_id",
            openapi.IN_PATH,
            description="ID of the current task status",
            type=openapi.TYPE_INTEGER,
            required=True,
        )
    ],
    responses={
        200: TaskStatusSerializer(many=True),
        404: "Not Found - Task status not found",
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
# pylint: disable=unused-argument
def list_next_task_statuses(
    request: Request, current_status_id: int
) -> Response:
    current_status = get_object_or_404(
        task_status.TaskStatus, id=current_status_id
    )

    try:
        next_statuses = current_status.children.all().order_by("order")
        serializer = TaskStatusSerializer(next_statuses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Failed to list next task statuses")
        return Response(
            {"error": f"Failed to list next task statuses: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
