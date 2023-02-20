from fastapi import APIRouter, status

from annotation.microservice_communication.search import \
    X_CURRENT_TENANT_HEADER
from annotation.schemas import EntitiesStatusesSchema
from annotation.tags import METADATA_TAG, TASKS_TAG

router = APIRouter(
    prefix="/metadata",
    tags=[TASKS_TAG, METADATA_TAG],
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=EntitiesStatusesSchema,
    summary="Get list of possible statuses of tasks.",
)
def get_entities_statuses(
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
):
    return EntitiesStatusesSchema()
