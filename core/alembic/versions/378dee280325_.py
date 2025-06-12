"""empty message

Revision ID: 378dee280325
Revises: 
Create Date: 2025-06-05 15:51:15.939395

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "378dee280325"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "core_plugins",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.Column("name", sa.String(32), nullable=False),
        sa.Column("version", sa.String(16), nullable=False),
        sa.Column("menu_name", sa.String(16), nullable=False),
        sa.Column("description", sa.String(10_000), nullable=True),
        sa.Column("url", sa.String(256), nullable=False),
        sa.Column("is_iframe", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "is_autoinstalled", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "version", name="uq_core_plugins_name_version"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("core_plugins")
