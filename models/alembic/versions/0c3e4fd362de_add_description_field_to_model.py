"""add description field to model

Revision ID: 0c3e4fd362de
Revises: b4c5225515f1
Create Date: 2022-05-18 12:43:20.709606

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0c3e4fd362de"
down_revision = "b4c5225515f1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "model",
        sa.Column("description", sa.VARCHAR(), server_default="", nullable=False),
    )


def downgrade():
    op.drop_column("model", "description")
