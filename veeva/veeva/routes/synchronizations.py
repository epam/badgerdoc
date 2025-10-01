import datetime
import logging
from typing import Optional

import filter_lib
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from tenant_dependency import TenantData

import veeva.core.db
import veeva.models
from veeva.veeva.routes.dependencies import require_admin_role

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/synchronization",
    tags=["synchronization"],
)


class SynchronizationCreateRequest(BaseModel):
    configuration_id: int


class SynchronizationCreateResponse(BaseModel):
    id: int


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def synchronize(
    request: SynchronizationCreateRequest,
    token_data: TenantData = Depends(require_admin_role),
    tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    session: AsyncSession = Depends(veeva.core.db.get_session),
) -> SynchronizationCreateResponse:
    try:
        new_synchronization = await veeva.services.synchronization.create(
            session=session,
            user=token_data.user_id,
            tenant=tenant,
            configuration_id=request.configuration_id,
        )
    except veeva.services.synchronization.SynchronizationNotFoundError:
        logger.error(
            "Configuration with ID %s not found for tenant %s",
            request.configuration_id,
            tenant,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )
    return SynchronizationCreateResponse(id=new_synchronization.id)


class Synchronization(BaseModel):
    id: int
    configuration_id: int
    status: str
    created_by: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


@router.get(
    "/{synchronization_id}",
)
async def get_synchronization(
    synchronization_id: int,
    _: TenantData = Depends(require_admin_role),
    tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    session: AsyncSession = Depends(veeva.core.db.get_session),
) -> Synchronization:
    """
    Retrieve a specific synchronization job by its ID.

    Args:
        synchronization_id: ID of the synchronization job to retrieve
        token_data: Tenant information from the authentication token
        tenant: Current tenant header
        session: Database session dependency

    Returns:
        Synchronization: The requested synchronization job details
    """
    logger.debug(
        "Retrieving synchronization with ID %d for tenant %s",
        synchronization_id,
        tenant,
    )
    try:
        sync = await veeva.services.synchronization.get_by_id(
            session, synchronization_id, tenant
        )
    except veeva.services.synchronization.SynchronizationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synchronization with ID {synchronization_id} not found",
        )
    return sync


SynchronizationSearchRequest = filter_lib.create_filter_model(
    veeva.models.orm.Synchronization
)


@router.post("/search")
async def search(
    request: SynchronizationSearchRequest,
    _: TenantData = Depends(require_admin_role),
    tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    session: Session = Depends(veeva.core.db.get_session_sync),
) -> filter_lib.Page[Synchronization]:
    try:
        query, pag = await veeva.services.synchronization.get_all_query(
            session, tenant, request.model_dump()
        )
    except Exception as e:
        logger.exception("Error processing synchronization search request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing request: {e}",
        )
    return filter_lib.paginate([x for x in query], pag)
