"""added previous_jobs field

Revision ID: 2dd22b64e1a9
Revises: ef5c796d3c00
Create Date: 2024-05-21 18:15:22.299757

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2dd22b64e1a9"
down_revision = "ef5c796d3c00"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "job",
        sa.Column(
            "previous_jobs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("job", "previous_jobs")
    # ### end Alembic commands ###
