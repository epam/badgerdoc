import enum
import typing
from datetime import datetime
from enum import StrEnum, auto

import sqlalchemy
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    type_annotation_map = {
        enum.Enum: sqlalchemy.Enum(enum.Enum),
        typing.Literal: sqlalchemy.Enum(enum.Enum),
    }


# TODO: should I change to literal?
class SyncProtocol(StrEnum):
    REST_API = auto()
    VAULT_LOADER = auto()


class SyncType(StrEnum):
    DOCUMENTS = auto()
    MAPPINGS = auto()


class Configuration(Base):
    """Model representing a Veeva PM configuration."""

    __tablename__ = "veeva_pm_configurations"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    tenant: Mapped[str] = mapped_column(String(32))
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_by: Mapped[str | None] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    sync_type: Mapped[str] = mapped_column(String(16))
    protocol: Mapped[str] = mapped_column(String(16))
    veeva_pm_host: Mapped[str] = mapped_column(String(2083))
    veeva_pm_login: Mapped[str] = mapped_column(String(255))
    veeva_pm_password: Mapped[str] = mapped_column(String(255))
    veeva_pm_vql: Mapped[str | None] = mapped_column(String(10_000))
    soft_deleted: Mapped[bool] = Column(sqlalchemy.Boolean, default=False)

    synchronizations: Mapped[list["Synchronization"]] = relationship(
        "Synchronization",
        back_populates="configuration",
    )

    def __repr__(self):
        return f"<Configuration(id={self.id}, tenant='{self.tenant}', sync_type='{self.sync_type}')>"


SynchronizationStatus = typing.Literal[
    "pending", "in_progress", "finished", "cancelled", "timed_out", "failed"
]


class Synchronization(Base):
    """Model representing a Veeva PM synchronization run."""

    __tablename__ = "veeva_pm_synchronization_runs"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    configuration_id: Mapped[int] = mapped_column(
        ForeignKey("veeva_pm_configurations.id")
    )
    configuration: Mapped["Configuration"] = relationship(
        "Configuration", back_populates="synchronizations"
    )
    status: Mapped[SynchronizationStatus] = mapped_column(
        Enum(
            *typing.get_args(SynchronizationStatus),
            name="veeva_pm_synchronization_status_enum",
        )
    )
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    synchronization_logs: Mapped[list["SynchronizationLog"]] = relationship(
        "SynchronizationLog", back_populates="synchronization"
    )

    def __repr__(self):
        return f"<Synchronization(id={self.id}, configuration_id={self.configuration_id}, status={self.status})>"


class SynchronizationLog(Base):
    """Model representing a log entry for a Veeva PM synchronization run."""

    __tablename__ = "veeva_pm_synchronization_log"
    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    synchronization_id: Mapped[int] = mapped_column(
        ForeignKey("veeva_pm_synchronization_runs.id")
    )
    synchronization: Mapped["Synchronization"] = relationship(
        "Synchronization", back_populates="synchronization_logs"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    message: Mapped[str] = mapped_column(String(10_000))
