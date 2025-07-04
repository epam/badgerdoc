import enum

import sqlalchemy
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime as SQLDateTime

Base = declarative_base()


class SyncProtocol(enum.StrEnum):
    RestAPI = "RestAPI"
    VaultLoader = "VaultLoader"


class SyncType(enum.StrEnum):
    Documents = "Documents"
    Mappings = "Mappings"


class Configuration(Base):
    """Model representing a Veeva PM configuration."""

    __tablename__ = "veeva_pm_configurations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(
        SQLDateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_by = Column(String, nullable=True)
    updated_at = Column(SQLDateTime(timezone=True), nullable=True)
    sync_type = Column(String, nullable=False)
    protocol = Column(String, nullable=False)
    veeva_pm_host = Column(String, nullable=False)
    veeva_pm_login = Column(String, nullable=False)
    veeva_pm_password = Column(String, nullable=False)
    veeva_pm_vql = Column(String, nullable=True)
    soft_deleted = Column(sqlalchemy.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Configuration(id={self.id}, tenant='{self.tenant}', sync_type='{self.sync_type}')>"
