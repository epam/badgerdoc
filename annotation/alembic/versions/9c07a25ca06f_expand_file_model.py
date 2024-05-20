"""Expand file model

Revision ID: 9c07a25ca06f
Revises: bda0eac5ce64
Create Date: 2021-12-01 18:03:43.404957

"""

from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9c07a25ca06f"
down_revision = "bda0eac5ce64"
branch_labels = None
depends_on = None


class FileStatusEnumSchema(str, Enum):
    pending = "Pending"
    ready = "Ready"
    annotated = "Annotated"
    validated = "Validated"


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "files",
        sa.Column(
            "distributed_annotating_pages",
            postgresql.ARRAY(sa.INTEGER()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "files",
        sa.Column(
            "annotated_pages",
            postgresql.ARRAY(sa.INTEGER()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "files",
        sa.Column(
            "distributed_validating_pages",
            postgresql.ARRAY(sa.INTEGER()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "files",
        sa.Column(
            "validated_pages",
            postgresql.ARRAY(sa.INTEGER()),
            nullable=False,
            server_default="{}",
        ),
    )
    # ### end Alembic commands ###
    file_status = postgresql.ENUM(FileStatusEnumSchema, name="file_status")
    file_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "files",
        sa.Column(
            "status",
            file_status,
            nullable=False,
            server_default=FileStatusEnumSchema.pending.name,
        ),
    )


def downgrade():
    op.drop_column("files", "status")
    op.execute("DROP TYPE file_status;")
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("files", "validated_pages")
    op.drop_column("files", "distributed_validating_pages")
    op.drop_column("files", "annotated_pages")
    op.drop_column("files", "distributed_annotating_pages")
    # ### end Alembic commands ###
