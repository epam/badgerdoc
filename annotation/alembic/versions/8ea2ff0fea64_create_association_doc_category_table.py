"""create association_doc_category table

Revision ID: 8ea2ff0fea64
Revises: 6fb3e0d231ff
Create Date: 2022-12-27 15:56:43.667409

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8ea2ff0fea64"
down_revision = "6fb3e0d231ff"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "association_doc_category",
        sa.Column("revision", sa.VARCHAR, primary_key=True),
        sa.Column("file_id", sa.INTEGER, primary_key=True),
        sa.Column("job_id", sa.INTEGER, primary_key=True),
        sa.Column(
            "category_id",
            sa.VARCHAR,
            sa.ForeignKey("categories.id"),
            primary_key=True,
        ),
        sa.ForeignKeyConstraint(
            ("revision", "file_id", "job_id"),
            (
                "annotated_docs.revision",
                "annotated_docs.file_id",
                "annotated_docs.job_id",
            ),
        ),
    )


def downgrade():
    op.drop_table("association_doc_category")
