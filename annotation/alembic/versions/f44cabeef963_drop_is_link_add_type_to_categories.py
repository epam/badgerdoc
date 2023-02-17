"""drop is_link add type to categories

Revision ID: f44cabeef963
Revises: 89276b8ebe84
Create Date: 2022-04-26 15:34:43.979807

"""
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "f44cabeef963"
down_revision = "89276b8ebe84"
branch_labels = None
depends_on = None


class CategoryTypeSchema(str, Enum):
    box = "box"
    link = "link"
    segmentation = "segmentation"


def upgrade():
    category_type = postgresql.ENUM(
        CategoryTypeSchema, name="categorytypeschema"
    )
    category_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "categories",
        sa.Column(
            "type",
            nullable=True,
            type_=category_type,
        ),
    )
    op.execute(
        "UPDATE categories SET type = CAST ('box' AS categorytypeschema)"
    )
    op.alter_column("categories", "type", nullable=False)
    op.drop_index("ix_categories_is_link", table_name="categories")
    op.drop_column("categories", "is_link")


def downgrade():
    op.add_column(
        "categories", sa.Column("is_link", sa.BOOLEAN(), nullable=True)
    )
    op.execute("UPDATE categories SET is_link = 'false'")
    op.alter_column("categories", "is_link", nullable=False)
    op.create_index(
        "ix_categories_is_link", "categories", ["is_link"], unique=False
    )
    op.drop_column("categories", "type")
    op.execute("DROP TYPE categorytypeschema;")
