# type: ignore
"""add webhook column

Revision ID: c26caf5e8a19
Revises: cd396f8a2df1
Create Date: 2022-02-25 16:40:53.725182

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c26caf5e8a19"
down_revision = "cd396f8a2df1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "pipeline_execution_task", sa.Column("webhook", sa.JSON, nullable=True)
    )


def downgrade():
    op.drop_column("pipeline_execution_task", "webhook")
