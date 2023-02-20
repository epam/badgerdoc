# type: ignore

"""remove token column

Revision ID: 08ad5deb23eb
Revises: c26caf5e8a19
Create Date: 2022-03-04 16:05:15.710853

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "08ad5deb23eb"
down_revision = "c26caf5e8a19"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("pipeline_execution_task", "token")


def downgrade():
    op.add_column(
        "pipeline_execution_task",
        sa.Column("token", sa.LargeBinary, nullable=True),
    )
