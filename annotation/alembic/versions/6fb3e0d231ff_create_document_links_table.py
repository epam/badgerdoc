"""create document links table

Revision ID: 6fb3e0d231ff
Revises: f1a58d769aa2
Create Date: 2022-12-27 15:24:53.927511

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "6fb3e0d231ff"
down_revision = "f1a58d769aa2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "document_links",
        sa.Column("original_revision", sa.VARCHAR),
        sa.Column("original_file_id", sa.INTEGER),
        sa.Column("original_job_id", sa.INTEGER),
        sa.Column("similar_revision", sa.VARCHAR),
        sa.Column("similar_file_id", sa.INTEGER),
        sa.Column("similar_job_id", sa.INTEGER),
        sa.Column(
            "label",
            sa.VARCHAR,
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ("original_revision", "original_file_id", "original_job_id"),
            (
                "annotated_docs.revision",
                "annotated_docs.file_id",
                "annotated_docs.job_id",
            ),
            ondelete="cascade",
        ),
        sa.ForeignKeyConstraint(
            ("similar_revision", "similar_file_id", "similar_job_id"),
            (
                "annotated_docs.revision",
                "annotated_docs.file_id",
                "annotated_docs.job_id",
            ),
            ondelete="cascade",
        ),
        sa.PrimaryKeyConstraint(
            "original_revision",
            "original_file_id",
            "original_job_id",
            "similar_revision",
            "similar_file_id",
            "similar_job_id",
        ),
    )


def downgrade():
    op.drop_table("document_links")
