"""Change file statuses

Revision ID: c06c594c7435
Revises: 2074c50e0af1
Create Date: 2021-12-14 13:26:18.778464

"""
from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c06c594c7435"
down_revision = "2074c50e0af1"
branch_labels = None
depends_on = None


class FileStatusEnumSchema(str, Enum):
    pending = "Pending"
    annotated = "Annotated"
    validated = "Validated"


def upgrade():
    op.alter_column("files", "status", type_=sa.VARCHAR(), server_default=None)
    op.execute("DROP TYPE file_status;")
    file_status = postgresql.ENUM(FileStatusEnumSchema, name="file_status")
    file_status.create(op.get_bind(), checkfirst=True)
    op.alter_column(
        "files",
        "status",
        type_=file_status,
        server_default=FileStatusEnumSchema.pending.name,
        postgresql_using="status::file_status",
    )


def downgrade():
    op.execute("ALTER TYPE file_status ADD VALUE 'ready'")
