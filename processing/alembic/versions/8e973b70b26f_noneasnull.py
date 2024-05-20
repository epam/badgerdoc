"""noneAsNull

Revision ID: 8e973b70b26f
Revises: 52af1473946f
Create Date: 2022-05-18 21:42:03.973476

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8e973b70b26f"
down_revision = "52af1473946f"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("preprocessing_tasks")
    op.create_table(
        "preprocessing_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("execution_id", sa.Integer(), nullable=True),
        sa.Column("chunk_id", sa.String(length=100), nullable=True),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("pipeline_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("execution_args", sa.JSON(none_as_null=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("preprocessing_tasks")
