import datetime
import enum

from sqlalchemy import (
    VARCHAR,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.types import ARRAY

from models.constants import DATABASE_URL

Base = declarative_base()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class StatusEnum(str, enum.Enum):
    READY = "ready"
    DEPLOYED = "deployed"


class Model(Base):  # type: ignore
    __tablename__ = "model"

    id = Column(String(15), primary_key=True)
    name = Column(String)
    basement = Column(
        String, ForeignKey("basement.id", ondelete="CASCADE"), nullable=False
    )
    data_path = Column(MutableDict.as_mutable(JSON), nullable=True)
    configuration_path = Column(MutableDict.as_mutable(JSON), nullable=True)
    training_id = Column(Integer, ForeignKey("training.id"), nullable=True)
    status = Column(Enum(StatusEnum), default="ready")
    score = Column(DOUBLE_PRECISION, nullable=True)
    categories = Column(MutableList.as_mutable(ARRAY(String)))
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
    tenant = Column(String(100))
    type = Column(String(100), nullable=True)
    description = Column(VARCHAR, nullable=False, server_default="")
    latest = Column(Boolean, nullable=False)
    version = Column(Integer, primary_key=True)

    base = relationship("Basement", back_populates="models")
    training = relationship("Training", back_populates="models")


class Basement(Base):  # type: ignore
    __tablename__ = "basement"

    id = Column(String(100), primary_key=True)
    name = Column(String)
    supported_args = Column(MutableList.as_mutable(ARRAY(JSON)), nullable=True)
    limits = Column(MutableDict.as_mutable(JSON), nullable=False)
    gpu_support = Column(Boolean)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
    tenant = Column(String(100))

    models = relationship(
        "Model", back_populates="base", cascade="all, delete, delete-orphan"
    )
    training = relationship(
        "Training",
        back_populates="bases",
        cascade="all, delete, delete-orphan",
    )
    key_script = Column(String)
    key_archive = Column(String)


class Training(Base):  # type: ignore
    __tablename__ = "training"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    jobs = Column(MutableList.as_mutable(ARRAY(Integer)))
    basement = Column(
        String, ForeignKey("basement.id", ondelete="CASCADE"), nullable=False
    )
    epochs_count = Column(Integer)
    kubeflow_pipeline_id = Column(String, nullable=True)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
    tenant = Column(String(100))
    key_archive = Column(String)

    models = relationship(
        "Model",
        back_populates="training",
        cascade="all, delete, delete-orphan",
    )
    bases = relationship("Basement", back_populates="training")
    key_annotation_dataset = Column(String)


def get_db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
