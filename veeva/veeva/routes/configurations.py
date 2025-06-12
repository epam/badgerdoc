import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import AnyHttpUrl, BaseModel, Field
from tenant_dependency import TenantData

import veeva.models.configuration
import veeva.services.configuration
import veeva.veeva.core.db
from veeva.veeva.routes.dependencies import require_admin_role

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/configurations",
    tags=["configurations"],
)


class ConfigurationCreateRequest(BaseModel):
    sync_type: veeva.models.configuration.SyncType
    protocol: veeva.models.configuration.SyncProtocol
    veeva_pm_host: AnyHttpUrl
    veeva_pm_login: str
    veeva_pm_password: str
    veeva_pm_vql: Optional[str] = Field(
        default=None,
        max_length=10_000,
        description="VQL query for filtering documents, max 10,000 characters",
    )


class ConfigurationResponse(BaseModel):
    id: int


class ConfigurationUpdateRequest(BaseModel):
    veeva_pm_host: AnyHttpUrl
    veeva_pm_login: str
    veeva_pm_password: str
    veeva_pm_vql: Optional[str] = Field(
        default=None,
        max_length=10_000,
        description="VQL query for filtering documents, max 10,000 characters",
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_configuration(
    config: ConfigurationCreateRequest,
    token_data: TenantData = Depends(require_admin_role),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(veeva.veeva.core.db.get_session),
) -> ConfigurationResponse:
    """
    Create a new Veeva PM configuration.

    Args:
        config: Configuration details
        token_data: Tenant information from the authentication token
        current_tenant: Current tenant header
        db_session: Database session dependency

    Returns:
        ConfigurationResponse with the ID of the created configuration
    """
    logger.debug("Creating configuration for tenant: %s", current_tenant)

    created_config = await veeva.services.configuration.create(
        session=db_session,
        user=token_data.user_id,
        tenant=current_tenant,
        sync_type=config.sync_type,
        protocol=config.protocol,
        veeva_pm_host=str(config.veeva_pm_host),
        veeva_pm_login=config.veeva_pm_login,
        veeva_pm_password=config.veeva_pm_password,
        veeva_pm_vql=config.veeva_pm_vql,
    )

    logger.info(
        "Configuration created successfully for tenant: %s, ID: %d",
        created_config.tenant,
        created_config.id,
    )

    return ConfigurationResponse(id=created_config.id)


@router.put(
    "/{config_id}",
    status_code=status.HTTP_200_OK,
)
async def update_configuration(
    config_id: int,
    config: ConfigurationUpdateRequest,
    token_data: TenantData = Depends(require_admin_role),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(veeva.veeva.core.db.get_session),
) -> ConfigurationResponse:
    """
    Update an existing Veeva PM configuration.

    Args:
        config_id: ID of the configuration to update
        config: Updated configuration details
        token_data: Tenant information from the authentication token
        current_tenant: Current tenant header
        db_session: Database session dependency

    Returns:
        ConfigurationResponse with the updated configuration ID
    """
    logger.debug(
        "Updating configuration ID %d for tenant: %s", config_id, current_tenant
    )
    try:
        await veeva.services.configuration.update(
            session=db_session,
            configuration_id=config_id,
            user=token_data.user_id,
            tenant=current_tenant,
            veeva_pm_host=str(config.veeva_pm_host),
            veeva_pm_login=config.veeva_pm_login,
            veeva_pm_password=config.veeva_pm_password,
            veeva_pm_vql=config.veeva_pm_vql,
        )
    except veeva.services.configuration.ConfigurationNotFoundError:
        logger.error(
            "Configuration ID %d not found for tenant: %s", config_id, current_tenant
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration with ID {config_id} not found",
        )
    logger.info(
        "Configuration ID %d updated successfully for tenant: %s",
        config_id,
        current_tenant,
    )
    return ConfigurationResponse(id=config_id)


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_configuration(
    config_id: int,
    token_data: TenantData = Depends(require_admin_role),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(veeva.veeva.core.db.get_session),
) -> ConfigurationResponse:
    """
    Soft delete a Veeva PM configuration.

    Args:
        config_id: ID of the configuration to delete
        token_data: Tenant information from the authentication token
        current_tenant: Current tenant header
        db_session: Database session dependency

    Returns:
        Success message indicating the configuration was deleted
    """
    logger.debug(
        "Deleting configuration ID %d for tenant: %s", config_id, current_tenant
    )
    try:
        await veeva.services.configuration.delete(
            session=db_session,
            configuration_id=config_id,
            tenant=current_tenant,
            user=token_data.user_id,
        )
    except veeva.services.configuration.ConfigurationNotFoundError:
        logger.error(
            "Configuration ID %d not found for tenant: %s", config_id, current_tenant
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration with ID {config_id} not found",
        )
    logger.info(
        "Configuration ID %d deleted successfully for tenant: %s",
        config_id,
        current_tenant,
    )
    return ConfigurationResponse(id=config_id)
