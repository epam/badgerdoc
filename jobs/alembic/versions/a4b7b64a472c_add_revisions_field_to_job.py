"""add revisions field to job

Revision ID: a4b7b64a472c
Revises: 2dd22b64e1a9
Create Date: 2024-09-11 17:40:41.052573

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a4b7b64a472c"
down_revision = "2dd22b64e1a9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "job",
        sa.Column(
            "revisions",
            sa.ARRAY(sa.String(50)),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade():
    op.drop_column("job", "revisions")
