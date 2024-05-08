"""add pipeline_engine

Revision ID: ef5c796d3c00
Revises: 1408c6c00120
Create Date: 2024-05-01 14:56:52.306791

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ef5c796d3c00"
down_revision = "1408c6c00120"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "job",
        sa.Column("pipeline_engine", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("job", "pipeline_engine")
