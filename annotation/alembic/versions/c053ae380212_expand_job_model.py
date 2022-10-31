"""Expand Job model

Revision ID: c053ae380212
Revises: 9c07a25ca06f
Create Date: 2021-12-06 10:36:27.187618

"""
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "c053ae380212"
down_revision = "9c07a25ca06f"
branch_labels = None
depends_on = None


class ValidationSchema(str, Enum):
    cross = "cross"
    hierarchical = "hierarchical"


def upgrade():
    op.rename_table("annotators", "users")
    op.create_table(
        "association_job_validator",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", sa.INTEGER(), nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.job_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "job_id"),
    )
    op.create_table(
        "association_job_owner",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", sa.INTEGER(), nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.job_id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "job_id"),
    )

    validation_type = postgresql.ENUM(ValidationSchema, name="validation_type")
    validation_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "jobs",
        sa.Column(
            "validation_type",
            validation_type,
            nullable=False,
            server_default=ValidationSchema.cross.name,
        ),
    )


def downgrade():
    op.drop_column("jobs", "validation_type")
    op.execute("DROP TYPE validation_type;")
    op.drop_table("association_job_owner")
    op.drop_table("association_job_validator")
    op.rename_table("users", "annotators")
