from typing import Any, Dict

from filter_lib import create_filter_model
from sqlalchemy import Boolean, Column, DateTime, Integer, String, inspect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from jobs.schemas import JobType

Base = declarative_base()


class Job(Base):  # type: ignore
    """Abstract class with common for
    AnnotationJobs and ExtractionJobs attributes"""

    __abstract__ = True

    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    status = Column(String(250))
    files = Column(JSONB)
    datasets = Column(JSONB)
    creation_datetime = Column(DateTime)
    type = Column(String(30))
    mode = Column(String(30))

    @property
    def as_dict(self) -> Dict[str, Any]:
        """Represents Job instance as a dict.
        Excludes key-value pair if value is None"""
        return {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
            if getattr(self, c.key) is not None
        }

    def __setitem__(self, key: Any, value: Any) -> None:
        self.key = value

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "job"}


class AnnotationJob(Job):
    __abstract__ = True

    annotators = Column(JSONB)
    validators = Column(JSONB)
    owners = Column(JSONB)
    categories = Column(JSONB)
    available_annotation_types = Column(JSONB, nullable=True)
    available_link_types = Column(JSONB, nullable=True)
    is_auto_distribution = Column(Boolean)
    deadline = Column(DateTime)
    validation_type = Column(String(30))
    extensive_coverage = Column(Integer, default=1)

    __mapper_args__ = {"polymorphic_identity": JobType.AnnotationJob.value}


class ExtractionJob(Job):
    __abstract__ = True
    all_files_data = Column(JSONB)
    pipeline_id = Column(String(250))
    pipeline_engine = Column(String(255))

    __mapper_args__ = {"polymorphic_identity": JobType.ExtractionJob.value}


class ImportJob(Job):
    __abstract__ = True
    import_source = Column(String(500))
    import_format = Column(String(50))


class CombinedJob(AnnotationJob, ExtractionJob, ImportJob):
    """Class to create 'job' table"""

    __tablename__ = "job"
    start_manual_job_automatically = Column(Boolean, nullable=True)


JobFilter = create_filter_model(CombinedJob, exclude=["all_files_data"])
