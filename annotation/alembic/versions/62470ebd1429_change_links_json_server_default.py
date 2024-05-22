"""change links_json server_default

Revision ID: 62470ebd1429
Revises: 3136551008d8
Create Date: 2023-02-21 18:39:00.462383

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "62470ebd1429"
down_revision = "3136551008d8"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "annotated_docs",
        "links_json",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=False,
        server_default="[]",
    )
    op.execute(
        "UPDATE annotated_docs SET links_json='[]' "
        "WHERE links_json::text='{}'::text"
    )


def downgrade():
    op.alter_column(
        "annotated_docs",
        "links_json",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text("'{}'::json"),
    )
    op.execute(
        "UPDATE annotated_docs SET links_json='{}' "
        "WHERE links_json::text='[]'::text"
    )
