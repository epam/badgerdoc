# type: ignore
"""add token column to execution_task table

Revision ID: 58fa5399caa9
Revises: 5fd9d1fdcf5b

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "58fa5399caa9"
down_revision = "5fd9d1fdcf5b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "pipeline_execution_task",
        sa.Column("token", sa.String(length=50), nullable=True),
    )


def downgrade():
    op.drop_column("pipeline_execution_task", "token")
