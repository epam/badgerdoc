"""add statuses to job

Revision ID: cf633ca94498
Revises: 8fbac489cef2
Create Date: 2022-02-12 22:03:46.728979

"""

from enum import Enum

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "cf633ca94498"
down_revision = "8fbac489cef2"
branch_labels = None
depends_on = None


class JobStatusEnumSchema(str, Enum):
    pending = "Pending"
    in_progress = "In Progress"
    finished = "Finished"
    failed = "Failed"


def upgrade():
    job_status = postgresql.ENUM(
        JobStatusEnumSchema, name="jobstatusenumschema"
    )
    job_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "jobs",
        sa.Column(
            "status",
            nullable=True,
            type_=job_status,
        ),
    )
    op.execute("UPDATE jobs SET status = 'finished'")
    op.alter_column("jobs", "status", nullable=False)


def downgrade():
    op.drop_column("jobs", "status")
    op.execute("DROP TYPE jobstatusenumschema;")
