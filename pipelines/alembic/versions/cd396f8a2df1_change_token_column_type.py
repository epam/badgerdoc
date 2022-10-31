# type: ignore
"""change token column type

Revision ID: cd396f8a2df1
Revises: 58fa5399caa9
Create Date: 2022-02-24 20:53:03.113701

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "cd396f8a2df1"
down_revision = "58fa5399caa9"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("pipeline_execution_task", "token")
    op.add_column(
        "pipeline_execution_task",
        sa.Column("token", sa.LargeBinary, nullable=True),
    )


def downgrade():
    op.drop_column("pipeline_execution_task", "token")
    op.add_column(
        "pipeline_execution_task",
        sa.Column("token", sa.String(length=50), nullable=True),
    )
