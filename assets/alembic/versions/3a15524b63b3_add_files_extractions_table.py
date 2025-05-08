"""add files_extractions table

Revision ID: 3a15524b63b3
Revises: 9e837ea0c11d
Create Date: 2025-04-28 15:17:32.323341

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3a15524b63b3"
down_revision = "9e837ea0c11d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "files_extractions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("engine", sa.String(length=150), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("file_extension", sa.String(length=5), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("last_modified", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("started", "finished", name="extractionstatus"),
            nullable=False,
            server_default="started",
        ),
        sa.ForeignKeyConstraint(
            ["file_id"], ["assets_files.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("files_extractions")
    op.execute("DROP TYPE IF EXISTS extractionstatus CASCADE;")
