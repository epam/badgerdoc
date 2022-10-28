import datetime
from typing import Any, Dict, Optional

import sqlalchemy as sa
from filter_lib import create_filter_model
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.engine.default import DefaultExecutionContext
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import TypeDecorator

from src.config import settings

Base = declarative_base()
engine = sa.create_engine(
    settings.database_url,
    pool_size=settings.sqlalchemy_pool_size,
    max_overflow=10,
    pool_recycle=3600,
    pool_use_lifo=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine)


def check_pages(context: DefaultExecutionContext) -> Optional[int]:
    current_params = context.get_current_parameters()
    mime: str = current_params.get("content_type", "")
    pages: Optional[int] = current_params.get("pages")
    if mime.startswith("image/") and pages is None:
        return 1
    return pages


class TSVector(TypeDecorator):  # type: ignore
    impl = TSVECTOR


class Association(Base):  # type: ignore

    __tablename__ = "association"

    dataset_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("datasets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    file_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("files.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow()
    )

    @property
    def as_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "file_id": self.file_id,
            "created": self.created,
        }


class Datasets(Base):  # type: ignore

    __tablename__ = "datasets"

    id = sa.Column(
        sa.Integer,
        autoincrement=True,
        primary_key=True,
        unique=True,
    )
    name = sa.Column(sa.String(150), nullable=False, unique=True)
    count = sa.Column(sa.Integer, default=0)
    created = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow()
    )
    ts_vector = sa.Column(
        TSVector(),
        sa.Computed(
            "to_tsvector('english', name)",
            persisted=True,
        ),
    )

    __table_args__ = (
        sa.Index("ix_ds_name", ts_vector, postgresql_using="gin"),
    )

    @property
    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "count": self.count,
            "created": self.created,
        }

    def __repr__(self) -> str:
        return f"{self.as_dict}"


class FileObject(Base):  # type: ignore

    __tablename__ = "files"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    original_name = sa.Column(sa.String(150), nullable=False)
    bucket = sa.Column(sa.String(65), nullable=False)
    size_in_bytes = sa.Column(sa.Integer, nullable=False)
    extension = sa.Column(sa.String(50), nullable=False)
    original_ext = sa.Column(sa.String(50), nullable=True)
    content_type = sa.Column(sa.String(150), nullable=False)
    pages = sa.Column(sa.Integer, default=check_pages)
    last_modified = sa.Column(
        sa.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    status = sa.Column(sa.String(50), nullable=False)
    ts_vector = sa.Column(
        TSVector(),
        sa.Computed(
            "to_tsvector('english', original_name)",
            persisted=True,
        ),
    )
    datasets = relationship(
        "Datasets", secondary="association", backref="files"
    )

    __table_args__ = (sa.Index("ix_name", ts_vector, postgresql_using="gin"),)

    @property
    def path(self) -> str:
        return f"files/{self.id}/{self.id}{self.extension}"

    @property
    def thumb_path(self) -> str:
        return f"files/{self.id}/1_w{settings.width}.jpg"

    @property
    def origin_path(self) -> str:
        return f"files/origins/{self.id}/{self.id}{self.original_ext}"

    @property
    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "original_name": self.original_name,
            "bucket": self.bucket,
            "size_in_bytes": self.size_in_bytes,
            "extension": self.extension,
            "original_ext": self.original_ext,
            "content_type": self.content_type,
            "pages": self.pages,
            "last_modified": self.last_modified,
            "status": self.status,
            "path": self.path,
            "datasets": [ds.name for ds in self.datasets],
        }

    def __repr__(self) -> str:
        return f"{self.as_dict}"


FileRequest = create_filter_model(FileObject)
DatasetRequest = create_filter_model(Datasets)
