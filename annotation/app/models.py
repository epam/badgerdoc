from sqlalchemy import (
    BOOLEAN,
    INTEGER,
    TIMESTAMP,
    VARCHAR,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Table,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSON, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy_utils import LtreeType

from app.database import Base
from app.schemas import (
    DEFAULT_LOAD,
    CategoryTypeSchema,
    FileStatusEnumSchema,
    JobStatusEnumSchema,
    JobTypeEnumSchema,
    TaskStatusEnumSchema,
    ValidationSchema,
)

association_job_annotator = Table(
    "association_job_annotator",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey("users.user_id", ondelete="cascade"),
        primary_key=True,
    ),
    Column(
        "job_id",
        ForeignKey("jobs.job_id", ondelete="cascade"),
        primary_key=True,
    ),
)
association_job_validator = Table(
    "association_job_validator",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey("users.user_id", ondelete="cascade"),
        primary_key=True,
    ),
    Column(
        "job_id",
        ForeignKey("jobs.job_id", ondelete="cascade"),
        primary_key=True,
    ),
)
association_job_owner = Table(
    "association_job_owner",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey("users.user_id", ondelete="cascade"),
        primary_key=True,
    ),
    Column(
        "job_id",
        ForeignKey("jobs.job_id", ondelete="cascade"),
        primary_key=True,
    ),
)
association_job_category = Table(
    "association_jobs_categories",
    Base.metadata,
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
    Column("job_id", ForeignKey("jobs.job_id"), primary_key=True),
)


class AnnotatedDoc(Base):
    __tablename__ = "annotated_docs"

    revision = Column(VARCHAR, primary_key=True)
    user = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL")
    )
    pipeline = Column(INTEGER)
    date = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    file_id = Column(INTEGER, primary_key=True)
    job_id = Column(INTEGER, primary_key=True)
    pages = Column(JSON, nullable=False, server_default="{}")
    failed_validation_pages = Column(
        ARRAY(INTEGER), nullable=False, server_default="{}"
    )
    validated = Column(ARRAY(INTEGER), nullable=False, server_default="{}")
    tenant = Column(VARCHAR, nullable=False)
    task_id = Column(INTEGER, ForeignKey("tasks.id", ondelete="SET NULL"))

    tasks = relationship("ManualAnnotationTask", back_populates="docs")


class Category(Base):
    __tablename__ = "categories"

    id = Column(VARCHAR, primary_key=True)
    tenant = Column(VARCHAR, nullable=True)
    name = Column(VARCHAR, nullable=False)
    parent = Column(
        VARCHAR,
        ForeignKey("categories.id", ondelete="cascade"),
        CheckConstraint("id != parent", name="self_parent_const"),
        nullable=True,
        index=True,
    )
    metadata_ = Column("metadata", JSONB, nullable=True)
    type = Column(ENUM(CategoryTypeSchema), nullable=False)
    editor = Column(VARCHAR, nullable=True)
    data_attributes = Column(ARRAY(JSONB), nullable=True)
    parent_id = relationship(
        "Category",
        remote_side=[id],
    )
    jobs = relationship(
        "Job", secondary=association_job_category, back_populates="categories"
    )
    tree = Column(LtreeType, nullable=True)
    __table_args__ = (Index("index_tree", tree, postgresql_using="gist"),)


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    default_load = Column(INTEGER, nullable=False, default=DEFAULT_LOAD)
    overall_load = Column(
        INTEGER,
        CheckConstraint("overall_load >= 0", name="not_negative_overall_load"),
        nullable=False,
        default=0,
    )
    tasks = relationship("ManualAnnotationTask", back_populates="user")
    job_annotators = relationship(
        "Job", secondary=association_job_annotator, back_populates="annotators"
    )
    job_validators = relationship(
        "Job", secondary=association_job_validator, back_populates="validators"
    )
    job_owners = relationship(
        "Job", secondary=association_job_owner, back_populates="owners"
    )


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(INTEGER, primary_key=True)
    name = Column(VARCHAR, nullable=True)
    job_type = Column(ENUM(JobTypeEnumSchema), nullable=True)
    is_auto_distribution = Column(BOOLEAN, nullable=False)
    callback_url = Column(VARCHAR, nullable=False)
    deadline = Column(TIMESTAMP)
    tenant = Column(VARCHAR, nullable=False)
    validation_type = Column(ENUM(ValidationSchema), nullable=False)
    status = Column(
        ENUM(JobStatusEnumSchema),
        nullable=False,
        default=JobStatusEnumSchema.pending,
    )
    tasks = relationship("ManualAnnotationTask", back_populates="jobs")
    files = relationship("File", back_populates="jobs")
    annotators = relationship(
        "User",
        secondary=association_job_annotator,
        back_populates="job_annotators",
    )
    validators = relationship(
        "User",
        secondary=association_job_validator,
        back_populates="job_validators",
    )
    owners = relationship(
        "User",
        secondary=association_job_owner,
        back_populates="job_owners",
    )

    categories = relationship("Category", secondary=association_job_category)


class File(Base):
    __tablename__ = "files"

    file_id = Column(INTEGER, primary_key=True)
    tenant = Column(VARCHAR, nullable=False)
    job_id = Column(INTEGER, ForeignKey("jobs.job_id"), primary_key=True)
    pages_number = Column(INTEGER, nullable=False)
    distributed_annotating_pages = Column(
        ARRAY(INTEGER),
        nullable=False,
        server_default="{}",
    )
    annotated_pages = Column(
        ARRAY(INTEGER),
        nullable=False,
        server_default="{}",
    )
    distributed_validating_pages = Column(
        ARRAY(INTEGER),
        nullable=False,
        server_default="{}",
    )
    validated_pages = Column(
        ARRAY(INTEGER),
        nullable=False,
        server_default="{}",
    )
    status = Column(
        ENUM(FileStatusEnumSchema),
        nullable=False,
        default=FileStatusEnumSchema.pending,
    )

    jobs = relationship("Job", back_populates="files")


class ManualAnnotationTask(Base):
    __tablename__ = "tasks"

    id = Column(INTEGER, primary_key=True)
    file_id = Column(INTEGER, nullable=False)
    pages = Column(ARRAY(INTEGER), nullable=False)
    job_id = Column(
        INTEGER, ForeignKey("jobs.job_id", ondelete="cascade"), nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    is_validation = Column(BOOLEAN, nullable=False)
    status = Column(
        ENUM(TaskStatusEnumSchema),
        nullable=False,
        default=TaskStatusEnumSchema.pending,
    )
    deadline = Column(TIMESTAMP)

    user = relationship("User", back_populates="tasks")
    jobs = relationship("Job", back_populates="tasks")
    docs = relationship("AnnotatedDoc", back_populates="tasks")
