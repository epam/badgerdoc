"""add_categories_editor_url_data_attributes

Revision ID: 1edef72a5043
Revises: 36bff2d016f7
Create Date: 2022-02-03 11:53:19.965523

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "1edef72a5043"
down_revision = "36bff2d016f7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "categories", sa.Column("editor_url", sa.VARCHAR(), nullable=True)
    )
    op.add_column(
        "categories",
        sa.Column(
            "data_attributes", postgresql.ARRAY(sa.VARCHAR()), nullable=True
        ),
    )


def downgrade():
    op.drop_column("categories", "data_attributes")
    op.drop_column("categories", "editor_url")
