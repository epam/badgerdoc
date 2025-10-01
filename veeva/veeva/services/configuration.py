"""Configuration service module for Veeva PM integration."""

import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from veeva.models import orm

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


class ConfigurationNotFoundError(Exception):
    pass


@dataclass
class Configuration:
    tenant: str

    id: int | None = None
    title: str | None = None
    veeva_pm_host: str | None = None
    veeva_pm_login: str | None = None
    veeva_pm_password: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_by: str | None = None
    updated_at: datetime | None = None
    sync_type: orm.SyncType | None = None
    protocol: orm.SyncProtocol | None = None
    veeva_pm_vql: str | None = None
    soft_deleted: bool | None = None

    def asdict(self) -> dict:
        return asdict(self)

    def from_orm(self, orm_config: orm.Configuration) -> "Configuration":
        data = {
            column.name: getattr(orm_config, column.name)
            for column in orm_config.__table__.columns
        }

        data["sync_type"] = orm.SyncType(data["sync_type"])
        data["protocol"] = orm.SyncProtocol(data["protocol"])
        return Configuration(**data)

    async def create(
        self,
        session: AsyncSession,
    ) -> "Configuration":
        logger.debug(
            "Creating Veeva PM configuration for tenant: %s", self.tenant
        )
        new_config = orm.Configuration(
            tenant=self.tenant,
            created_by=self.created_by,
            title=self.title,
            sync_type=self.sync_type.value,
            protocol=self.protocol.value,
            veeva_pm_host=self.veeva_pm_host,
            veeva_pm_login=self.veeva_pm_login,
            veeva_pm_password=self.veeva_pm_password,
            veeva_pm_vql=self.veeva_pm_vql,
        )
        session.add(new_config)
        await session.commit()
        await session.refresh(
            new_config
        )  # Refresh to get the ID from the database

        logger.debug(
            "Created new Veeva PM configuration with ID %d for tenant %s",
            new_config.id,
            self.tenant,
        )
        return self.from_orm(new_config)

    async def update(
        self,
        session: AsyncSession,
    ) -> "Configuration":
        logger.debug(
            "Updating Veeva PM configuration ID %d for tenant %s",
            self.id,
            self.tenant,
        )

        stmt = (
            sqlalchemy.update(orm.Configuration)
            .where(
                (orm.Configuration.id == self.id)
                & (~orm.Configuration.soft_deleted)
                & (orm.Configuration.tenant == self.tenant)
            )
            .values(
                updated_by=self.updated_by,
                updated_at=datetime.now(timezone.utc),
                veeva_pm_host=self.veeva_pm_host,
                veeva_pm_login=self.veeva_pm_login,
                veeva_pm_vql=self.veeva_pm_vql,
                **(
                    {"veeva_pm_password": self.veeva_pm_password}
                    if self.veeva_pm_password is not None
                    else {}
                ),
            )
            .returning(orm.Configuration)
        )

        result = await session.execute(stmt)
        config_record = result.scalar_one_or_none()
        if config_record is None:
            raise ConfigurationNotFoundError(
                f"Configuration with ID {self.id} not found or already soft deleted"
            )

        updated_config = self.from_orm(config_record)
        await session.commit()
        return updated_config

    async def delete(
        self,
        session: AsyncSession,
    ) -> "Configuration":
        logger.info("Soft deleting Veeva PM configuration ID %d", self.id)

        stmt = (
            sqlalchemy.update(orm.Configuration)
            .where(
                (orm.Configuration.id == self.id)
                & (~orm.Configuration.soft_deleted)
                & (orm.Configuration.tenant == self.tenant)
            )
            .values(
                updated_by=self.updated_by,
                soft_deleted=True,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(orm.Configuration)
        )

        result = await session.execute(stmt)
        config_record = result.scalar_one_or_none()

        if config_record is None:
            raise ConfigurationNotFoundError(
                f"Configuration with ID {self.id} not found or already soft deleted"
            )

        logger.info("Soft deleted Veeva PM configuration ID %d", self.id)
        deleted_config = self.from_orm(config_record)
        await session.commit()
        return deleted_config

    async def get(
        self,
        session: AsyncSession,
    ) -> "Configuration":
        logger.debug(
            "Retrieving Veeva PM configuration ID %d for tenant %s",
            self.id,
            self.tenant,
        )

        stmt = sqlalchemy.select(orm.Configuration).where(
            (orm.Configuration.id == self.id)
            & (~orm.Configuration.soft_deleted)
            & (orm.Configuration.tenant == self.tenant)
        )

        result = await session.execute(stmt)
        config = result.scalar_one_or_none()

        if config is None:
            raise ConfigurationNotFoundError(
                f"Configuration with ID {self.id} not found or soft deleted"
            )

        logger.debug("Retrieved Veeva PM configuration ID %d", self.id)
        return self.from_orm(config)

    async def get_all(self, session: AsyncSession) -> list["Configuration"]:
        logger.debug(
            "Retrieving all Veeva PM configurations for tenant %s", self.tenant
        )

        stmt = sqlalchemy.select(orm.Configuration).where(
            orm.Configuration.tenant == self.tenant,
            ~orm.Configuration.soft_deleted,
        )

        result = await session.execute(stmt)
        configs = result.scalars().all()

        return [self.from_orm(config) for config in configs]
