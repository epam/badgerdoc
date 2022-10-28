"""renamed_column

Revision ID: f637b13c744d
Revises: 8e973b70b26f
Create Date: 2022-05-19 12:43:52.309487

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f637b13c744d"
down_revision = "8e973b70b26f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preprocessing_tasks",
        sa.Column("batch_id", sa.String(length=100), nullable=True),
    )
    op.drop_column("preprocessing_tasks", "chunk_id")


def downgrade() -> None:
    op.add_column(
        "preprocessing_tasks",
        sa.Column(
            "chunk_id",
            sa.VARCHAR(length=100),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.drop_column("preprocessing_tasks", "batch_id")
