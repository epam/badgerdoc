"""category_change_editor_data_attribut
es

Revision ID: 8fbac489cef2
Revises: 1edef72a5043
Create Date: 2022-02-15 19:49:53.345305

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "8fbac489cef2"
down_revision = "1edef72a5043"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("categories", "editor_url", new_column_name="editor")
    op.alter_column(
        "categories",
        "data_attributes",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        type_=postgresql.ARRAY(postgresql.JSONB(astext_type=sa.Text())),
        existing_nullable=True,
        postgresql_using="data_attributes::jsonb[]",
    )


def downgrade():
    op.alter_column("categories", "editor", new_column_name="editor_url")
    op.alter_column(
        "categories",
        "data_attributes",
        existing_type=postgresql.ARRAY(postgresql.JSONB(astext_type=sa.Text())),
        type_=postgresql.ARRAY(sa.VARCHAR()),
        existing_nullable=True,
    )
