import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from tenant_dependency import TenantData

import veeva.veeva.core.db
from veeva.services import configuration
from veeva.veeva.routes.dependencies import require_admin_role

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/configurations",
    tags=["configurations"],
)


class ConfigurationCreateRequest(BaseModel):
    title: str
    sync_type: veeva.models.orm.SyncType
    protocol: veeva.models.orm.SyncProtocol
    veeva_pm_host: HttpUrl
    veeva_pm_login: str = Field(max_length=255)
    veeva_pm_password: str = Field(max_length=255)
    veeva_pm_vql: Optional[str] = Field(
        default=None,
        max_length=10_000,
        description="VQL query for filtering documents, max 10,000 characters",
    )


class ConfigurationUpdateRequest(BaseModel):
    title: str = Field(max_length=255)
    veeva_pm_host: HttpUrl
    veeva_pm_login: str = Field(max_length=255)
    veeva_pm_password: str | None = Field(max_length=255, default=None)
    veeva_pm_vql: Optional[str] = Field(
        default=None,
        max_length=10_000,
        description="VQL query for filtering documents, max 10,000 characters",
    )


class ConfigurationResponse(BaseModel):
    id: int
    tenant: str
    title: str
    sync_type: veeva.models.orm.SyncType
    protocol: veeva.models.orm.SyncProtocol
    created_by: str
    created_at: datetime
    veeva_pm_host: str
    veeva_pm_login: str
    veeva_pm_vql: str | None = None
    updated_by: str | None = None
    updated_at: datetime | None = None


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

        The config object should contain:
        * title: The title of the configuration (required)
        * sync_type: Synchronization type (required)
        * protocol: Synchronization protocol (required)
        * veeva_pm_host: URL of the Veeva PM host (required)
        * veeva_pm_login: Login username for Veeva PM (required)
        * veeva_pm_password: Password for Veeva PM (required)
        * veeva_pm_vql: VQL query for filtering documents (optional)

    Returns:
        The created configuration with all its details
    """
    logger.debug("Creating configuration for tenant: %s", current_tenant)

    created_config = await configuration.Configuration(
        created_by=token_data.user_id,
        tenant=current_tenant,
        title=config.title,
        sync_type=config.sync_type,
        protocol=config.protocol,
        veeva_pm_host=str(config.veeva_pm_host),
        veeva_pm_login=config.veeva_pm_login,
        veeva_pm_password=config.veeva_pm_password,
        veeva_pm_vql=config.veeva_pm_vql,
    ).create(
        session=db_session,
    )

    logger.info(
        "Configuration created successfully for tenant: %s, ID: %d",
        created_config.tenant,
        created_config.id,
    )

    return ConfigurationResponse(**created_config.asdict())


@router.get("/{config_id}")
async def get_configuration(
    config_id: int,
    _: TenantData = Depends(require_admin_role),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(veeva.veeva.core.db.get_session),
) -> ConfigurationResponse:
    """
    Get a specific Veeva PM configuration by ID.

    Args:

        *config_id: ID of the configuration to retrieve

    Returns:

        Configuration details with the following information:

        * id: Configuration identifier
        * title: The title of the configuration
        * sync_type: Synchronization type
        * protocol: Synchronization protocol
        * veeva_pm_host: URL of the Veeva PM host
        * veeva_pm_login: Login username for Veeva PM
        * veeva_pm_vql: VQL query for filtering documents (if configured)
        * created_by: User who created the configuration
        * created_at: When the configuration was created
        * updated_by: User who last updated the configuration (if updated)
        * updated_at: When the configuration was last updated (if updated)

    Raises:
        404: If the configuration with the specified ID doesn't exist
    """
    logger.debug(
        "Retrieving configuration with ID %d for tenant: %s",
        config_id,
        current_tenant,
    )
    try:
        config = await configuration.Configuration(
            id=config_id, tenant=current_tenant
        ).get(session=db_session)
    except configuration.ConfigurationNotFoundError:
        logger.error(
            "Configuration ID %d not found for tenant: %s",
            config_id,
            current_tenant,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration with ID {config_id} not found",
        )
    logger.info(
        "Configuration ID %d retrieved successfully for tenant: %s",
        config_id,
        current_tenant,
    )
    return ConfigurationResponse(**config.asdict())


@router.get("")
async def list_configurations(
    _: TenantData = Depends(require_admin_role),
    current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    db_session=Depends(veeva.veeva.core.db.get_session),
) -> list[ConfigurationResponse]:
    """
    List all Veeva PM configurations for the current tenant.

    Returns:

        List of configurations with the following information:

        * id: Configuration identifier
        * title: The title of the configuration
        * sync_type: Synchronization type
        * protocol: Synchronization protocol
        * veeva_pm_host: URL of the Veeva PM host
        * veeva_pm_login: Login username for Veeva PM
        * veeva_pm_vql: VQL query for filtering documents (if configured)
        * created_by: User who created the configuration
        * created_at: When the configuration was created
        * updated_by: User who last updated the configuration (if updated)
        * updated_at: When the configuration was last updated (if updated)

    """
    logger.debug("Listing configurations for tenant: %s", current_tenant)
    try:
        configs = await configuration.Configuration(
            tenant=current_tenant
        ).get_all(session=db_session)
    except configuration.ConfigurationNotFoundError:
        logger.error("No configurations found for tenant: %s", current_tenant)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No configurations found",
        )
    logger.info(
        "Retrieved configurations for tenant: %s",
        current_tenant,
    )
    return [ConfigurationResponse(**config.asdict()) for config in configs]


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

        The config object should contain:
        * title: The title of the configuration (required)
        * veeva_pm_host: URL of the Veeva PM host (required)
        * veeva_pm_login: Login username for Veeva PM (required)
        * veeva_pm_password: Password for Veeva PM (only include if changing)
        * veeva_pm_vql: VQL query for filtering documents (optional)

    Returns:
        Updated configuration details

    Important:
        All fields must always be sent in the request except for veeva_pm_password.
        The veeva_pm_password field should only be included if changing the password.
        For security reasons, the API never returns the password to the client.
    """
    logger.debug(
        "Updating configuration ID %d for tenant: %s",
        config_id,
        current_tenant,
    )
    try:
        updated_config = await configuration.Configuration(
            id=config_id,
            title=config.title,
            updated_by=token_data.user_id,
            tenant=current_tenant,
            veeva_pm_host=str(config.veeva_pm_host),
            veeva_pm_login=config.veeva_pm_login,
            veeva_pm_password=config.veeva_pm_password,
            veeva_pm_vql=config.veeva_pm_vql,
        ).update(
            session=db_session,
        )
    except configuration.ConfigurationNotFoundError:
        logger.error(
            "Configuration ID %d not found for tenant: %s",
            config_id,
            current_tenant,
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
    return ConfigurationResponse(**updated_config.asdict())


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

    This operation marks the configuration as deleted but doesn't remove it from the database.

    Args:
        config_id: ID of the configuration to delete

    Returns:
        Basic information about the deleted configuration

    Raises:
        404: If the configuration with the specified ID doesn't exist
    """
    logger.debug(
        "Deleting configuration ID %d for tenant: %s",
        config_id,
        current_tenant,
    )
    try:
        deleted_config = await configuration.Configuration(
            id=config_id,
            tenant=current_tenant,
            updated_by=token_data.user_id,
        ).delete(
            session=db_session,
        )
    except configuration.ConfigurationNotFoundError:
        logger.error(
            "Configuration ID %d not found for tenant: %s",
            config_id,
            current_tenant,
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
    return ConfigurationResponse(id=deleted_config.id)
