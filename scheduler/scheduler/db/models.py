import datetime
import uuid
from typing import Any, Dict, List, Type, Union

import sqlalchemy
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext import declarative

Base = declarative.declarative_base(metadata=sqlalchemy.MetaData())


class Unit(Base):  # type: ignore
    __tablename__ = "units"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    runner_id = sqlalchemy.Column(postgresql.UUID())
    url = sqlalchemy.Column(sqlalchemy.String)
    body = sqlalchemy.Column(sqlalchemy.JSON(none_as_null=True))
    tenant = sqlalchemy.Column(sqlalchemy.String)
    response_topic = sqlalchemy.Column(sqlalchemy.String)
    result = sqlalchemy.Column(sqlalchemy.JSON(none_as_null=True))
    status = sqlalchemy.Column(sqlalchemy.String)
    created = sqlalchemy.Column(
        sqlalchemy.DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    updated = sqlalchemy.Column(
        sqlalchemy.DateTime, onupdate=datetime.datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<Unit(id={self.id!r}, runner_id={self.runner_id!r}, "
            f"url={self.url!r}, body={self.body!r}, "
            f"tenant={self.tenant!r}, response_topic={self.response_topic!r}, "
            f"result={self.result!r}, status={self.status!r}, "
            f"created={self.created!r}, updated={self.updated!r}>"
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "body": self.body,
            "tenant": self.tenant,
            "response_topic": self.response_topic,
        }


class Heartbeat(Base):  # type: ignore
    __tablename__ = "heartbeat"

    id = sqlalchemy.Column(
        postgresql.UUID(), primary_key=True, default=uuid.uuid4
    )
    last_heartbeat = sqlalchemy.Column(
        sqlalchemy.DateTime, nullable=False, default=datetime.datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<Heartbeat(id={repr(self.id)!r}, "
            f"last_heartbeat={repr(self.last_heartbeat)!r})>"
        )

    def as_dict(
        self, iso_time: bool = False
    ) -> Dict[str, Union[uuid.UUID, datetime.datetime]]:
        """Return dict representation."""
        return {
            "id": self.id,
            "last_heartbeat": self.last_heartbeat.isoformat()
            if iso_time
            else self.last_heartbeat,
        }


Table = Union[Unit, Heartbeat]
TablesList = List[Table]
TableType = Type[Table]
