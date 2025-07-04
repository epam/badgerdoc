import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import AnyHttpUrl, BaseModel, Field
from tenant_dependency import TenantData

from veeva.veeva.routes.dependencies import require_admin_role

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/synchronization",
    tags=["synchronization"],
)


class SynchronizationRequest(BaseModel):
    configuration_id: int


class SynchronizationResponse(BaseModel):
    id: int


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def synchronize(
    request: SynchronizationRequest,
    token_data: TenantData = Depends(require_admin_role),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
) -> SynchronizationResponse:
    pass
