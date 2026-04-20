import logging

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_admin = serializers.BooleanField()


@swagger_auto_schema(
    method="get",
    operation_description="Retrieve the current user's details.",
    operation_summary="Get current user details",
    tags=["User"],
    responses={
        200: openapi.Response(
            description="User details",
            schema=UserSerializer(),
        ),
        401: "Unauthorized - Authentication required",
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user_info(request):
    try:
        user = request.user
        serializer = UserSerializer(
            {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_admin": user.is_superuser or user.is_staff,
            }
        )
        return Response(serializer.data, status=200)
    except Exception as e:
        logger.exception("Failed to retrieve user details")
        return Response(
            {"error": f"Failed to retrieve user details: {str(e)}"},
            status=500,
        )
