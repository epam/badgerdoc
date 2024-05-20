"""Add name and job_type to job model

Revision ID: 416952520dc1
Revises: cf633ca94498
Create Date: 2022-03-25 12:43:08.211806

"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "416952520dc1"
down_revision = "cf633ca94498"
branch_labels = None
depends_on = None


class JobTypeEnumSchema(str, Enum):
    ExtractionJob = "ExtractionJob"
    ExtractionWithAnnotationJob = "ExtractionWithAnnotationJob"
    AnnotationJob = "AnnotationJob"
    ImportJob = "ImportJob"


def upgrade():
    """Adds name and job_type to job entity"""
    job_type = postgresql.ENUM(JobTypeEnumSchema, name="jobtypeenumschema")
    job_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "jobs",
        sa.Column("job_type", nullable=True, type_=job_type),
    )
    op.add_column("jobs", sa.Column("name", sa.VARCHAR(), nullable=True))


def downgrade():
    op.drop_column("jobs", "job_type")
    op.drop_column("jobs", "name")
    op.execute("DROP TYPE jobtypeenumschema;")
