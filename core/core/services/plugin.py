import logging
import os
from typing import Optional

import sqlalchemy
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import orm

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


class PluginNotFoundError(Exception):
    pass


class PluginAlreadyExistsError(Exception):
    pass


class Plugin(BaseModel):
    name: str | None = None
    menu_name: str | None = None
    description: str | None = None
    version: str | None = None
    url: str | None = None
    is_iframe: bool = False
    is_autoinstalled: bool = False
    tenant: Optional[str] = None
    id: Optional[int] = None

    def from_orm(self, orm_plugin: orm.Plugin) -> "Plugin":
        return Plugin(
            **{
                column.name: getattr(orm_plugin, column.name)
                for column in orm_plugin.__table__.columns
            }
        )

    async def register(
        self,
        session: AsyncSession,
    ) -> "Plugin":
        logger.debug(
            "Registering plugin '%s' for tenant: %s", self.name, self.tenant
        )
        tenant = self.tenant or "*"
        new_plugin = orm.Plugin(
            tenant=tenant,
            name=self.name,
            menu_name=self.menu_name,
            description=self.description,
            version=self.version,
            url=self.url,
            is_iframe=self.is_iframe,
            is_autoinstalled=self.is_autoinstalled,
        )
        try:
            session.add(new_plugin)
            await session.commit()
        except sqlalchemy.exc.IntegrityError:
            logger.error(
                "Plugin '%s' already exists for tenant %s", self.name, tenant
            )
            raise PluginAlreadyExistsError(
                f"Plugin with name '{self.name}' already exists for tenant: {tenant}"
            )
        await session.refresh(new_plugin)
        logger.info(
            "Created new plugin '%s' for tenant: %s", self.name, tenant
        )
        return self.from_orm(new_plugin)

    async def get_all(self, db_session: AsyncSession) -> list[orm.Plugin]:
        result = await db_session.execute(
            orm.Plugin.__table__.select().where(
                orm.Plugin.tenant == self.tenant
            )
        )
        plugins = result.all()
        logger.debug(
            "Retrieved %d plugins for tenant: %s", len(plugins), self.tenant
        )
        return plugins

    async def update(
        self,
        db_session: AsyncSession,
    ) -> "Plugin":
        logger.debug("Updating plugin %d for tenant: %s", self.id, self.tenant)

        stmt = (
            sqlalchemy.update(orm.Plugin)
            .where(orm.Plugin.id == self.id)
            .where(orm.Plugin.tenant == self.tenant)
            .values(
                menu_name=self.menu_name,
                description=self.description,
                url=self.url,
                is_iframe=self.is_iframe,
                is_autoinstalled=self.is_autoinstalled,
            )
            .returning(orm.Plugin)
        )

        result = await db_session.execute(stmt)
        plugin_record = result.scalar_one_or_none()

        if not plugin_record:
            logger.warning(
                "Plugin %d not found for tenant: %s", self.id, self.tenant
            )
            raise PluginNotFoundError(
                f"Plugin with ID {self.id} not found for tenant {self.tenant}"
            )

        updated_plugin = self.from_orm(plugin_record)
        await db_session.commit()
        return updated_plugin

    async def delete_plugin(self, db_session: AsyncSession) -> "Plugin":
        """
        Delete a plugin from the database using a direct SQL DELETE statement.

        Args:
            db_session: SQLAlchemy AsyncSession for database operations

        Returns:
            Plugin: The deleted plugin object
        """
        logger.debug("Deleting plugin %d for tenant: %s", self.id, self.tenant)

        # Create DELETE statement with RETURNING clause to get deleted data
        delete_stmt = (
            sqlalchemy.delete(orm.Plugin)
            .where(orm.Plugin.id == self.id)
            .where(orm.Plugin.tenant == self.tenant)
        )

        # Add RETURNING clause to get the deleted object
        delete_stmt = delete_stmt.returning(orm.Plugin)

        # Execute the DELETE statement
        result = await db_session.execute(delete_stmt)
        deleted_record = result.scalar_one_or_none()

        if not deleted_record:
            logger.warning(
                "Plugin %d not found for tenant: %s", self.id, self.tenant
            )
            raise PluginNotFoundError(
                f"Plugin with ID {self.id} not found for tenant: {self.tenant}"
            )

        # Create Plugin instance from the deleted record
        deleted_plugin = self.from_orm(deleted_record)

        # Commit the transaction
        await db_session.commit()

        return deleted_plugin
