"""make document categories an array of strings

Revision ID: 9083dea3783e
Revises: 8ea2ff0fea64
Create Date: 2022-12-28 18:51:37.060169

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9083dea3783e"
down_revision = "8ea2ff0fea64"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "annotated_docs",
        sa.Column(
            "categories",
            sa.ARRAY(sa.VARCHAR),
            nullable=False,
            server_default="{}",
        ),
    )
    op.drop_table("association_doc_category")


def downgrade():
    op.drop_column("annotated_docs", "categories")
