# type: ignore
"""add original_ext column to files table

Revision ID: 0f6c859c1d1c
Revises: fe5926249504
Create Date: 2022-01-31 17:03:20.077985

"""
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from sqlalchemy.orm import Session  # noqa

from alembic import op
from src.db.models import FileObject  # noqa

revision = "0f6c859c1d1c"
down_revision = "fe5926249504"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "files", sa.Column("original_ext", sa.String(length=50), nullable=True)
    )


def downgrade():
    op.drop_column("files", "original_ext")
