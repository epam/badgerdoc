"""add available_annotation_types and
 available_link_types fields to CombinedJob model

Revision ID: 1408c6c00120
Revises: f60dd492b17f
Create Date: 2023-06-05 13:41:38.518903

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1408c6c00120"
down_revision = "f60dd492b17f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "job",
        sa.Column(
            "available_annotation_types",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "job",
        sa.Column(
            "available_link_types",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("job", "available_link_types")
    op.drop_column("job", "available_annotation_types")
    # ### end Alembic commands ###
