import uuid
from datetime import datetime
from typing import Any, Dict, List, Type, Union

import sqlalchemy as sa
from filter_lib import create_filter_model
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import relationship

Base: DeclarativeMeta = declarative_base()


class Pipeline(Base):  # type: ignore
    __tablename__ = "pipeline"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False, default=lambda: str(uuid.uuid4()))
    version = sa.Column(sa.Integer, nullable=True)
    original_pipeline_id = sa.Column(sa.Integer, nullable=True)
    is_latest = sa.Column(sa.Boolean, default=True, nullable=True)
    type = sa.Column(sa.String(30), nullable=True)
    description = sa.Column(sa.Text, nullable=True, default=None)
    summary = sa.Column(sa.Text, nullable=True, default=None)
    date = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)
    meta = sa.Column(sa.JSON(none_as_null=True))
    steps = sa.Column(sa.JSON(none_as_null=True))
    tasks = relationship(
        "PipelineExecutionTask",
        backref="pipeline",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Pipeline(id={self.id}, name={self.name!r}, "
            f"version={self.version!r}, type={self.type!r}, "
            f"date={self.date!r})>"
        )

    def as_dict(self, iso_time: bool = False) -> Dict[str, Any]:
        """Return dict representation."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "original_pipeline_id": self.original_pipeline_id,
            "is_latest": self.is_latest,
            "type": self.type,
            "description": self.description,
            "summary": self.summary,
            "date": self.date.isoformat() if iso_time else self.date,
            "meta": self.meta,
            "steps": self.steps,
        }


class PipelineExecutionTask(Base):  # type: ignore
    __tablename__ = "pipeline_execution_task"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False, default=lambda: str(uuid.uuid4()))
    date = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)
    pipeline_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("pipeline.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id = sa.Column(sa.Integer, index=True)
    runner_id = sa.Column(UUID())
    status = sa.Column(sa.String(30))
    steps = relationship(
        "ExecutionStep",
        backref="task",
        lazy="subquery",
        cascade="all, delete-orphan",
    )
    webhook = sa.Column(sa.String)

    def __repr__(self) -> str:
        return (
            f"<PipelineExecutionTask(id={self.id}, name={repr(self.name)}, "
            f"pipeline_id={self.pipeline_id}, job_id={self.job_id}, "
            f"runner_id={repr(self.runner_id)}, status={repr(self.status)})>"
        )

    def as_dict(self, iso_time: bool = False) -> Dict[str, Any]:
        """Return dict representation."""
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date.isoformat() if iso_time else self.date,
            "pipeline_id": self.pipeline_id,
            "job_id": self.job_id,
            "runner_id": self.runner_id,
            "status": self.status,
            "webhook": self.webhook,
        }


class ExecutionStep(Base):  # type: ignore
    __tablename__ = "execution_step"

    id = sa.Column(sa.Integer, primary_key=True)
    task_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("pipeline_execution_task.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name = sa.Column(sa.String(50), nullable=False, default=lambda: str(uuid.uuid4()))
    step_id = sa.Column(UUID())
    parent_step = sa.Column(UUID(), nullable=True)
    date = sa.Column(
        sa.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    init_args = sa.Column(sa.JSON(none_as_null=True))
    status = sa.Column(sa.String(30))
    result = sa.Column(sa.JSON(none_as_null=True))
    tenant = sa.Column(sa.String(50))

    def __repr__(self) -> str:
        return (
            f"<ExecutionStep(id={self.id}, task_id={self.task_id}, "
            f"name={repr(self.name)}, step_id={repr(self.step_id)}, "
            f"status={repr(self.status)})>"
        )

    def as_dict(self, iso_time: bool = False) -> Dict[str, Any]:
        """Return dict representation."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "name": self.name,
            "step_id": self.step_id,
            "parent_step": self.parent_step,
            "date": self.date.isoformat() if iso_time else self.date,
            "init_args": self.init_args,
            "status": self.status,
            "result": self.result,
            "tenant": self.tenant,
        }


class ExecutorHeartbeat(Base):  # type: ignore
    __tablename__ = "heartbeat"

    id = sa.Column(UUID(), primary_key=True, default=uuid.uuid4)
    last_heartbeat = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<ExecutorHeartbeat(id={repr(self.id)}, "
            f"last_heartbeat={repr(self.last_heartbeat)})>"
        )

    def as_dict(self, iso_time: bool = False) -> Dict[str, Any]:
        """Return dict representation."""
        return {
            "id": self.id,
            "last_heartbeat": self.last_heartbeat.isoformat()
            if iso_time
            else self.last_heartbeat,
        }


class MainEventLog(Base):  # type: ignore
    __tablename__ = "main_event_log"

    id = sa.Column(sa.Integer, primary_key=True)
    date = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)
    runner_id = sa.Column(UUID())
    event = sa.Column(JSONB(none_as_null=True))


PipelineFilter = create_filter_model(Pipeline, exclude=["meta", "steps"])

Table = Union[
    Pipeline,
    PipelineExecutionTask,
    ExecutionStep,
    ExecutorHeartbeat,
]
TablesList = List[Table]
TableType = Type[Table]
