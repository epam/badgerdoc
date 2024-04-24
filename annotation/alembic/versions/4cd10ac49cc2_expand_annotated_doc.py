"""expand annotated doc

Revision ID: 4cd10ac49cc2
Revises: c053ae380212
Create Date: 2021-12-07 18:45:24.282853

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "4cd10ac49cc2"
down_revision = "c053ae380212"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "annotated_docs",
        sa.Column(
            "failed_validation_pages",
            postgresql.ARRAY(sa.INTEGER()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "annotated_docs",
        sa.Column("task_id", sa.INTEGER(), nullable=True),
    )
    sa.ForeignKeyConstraint(
        ["task_id"],
        ["tasks.id"],
    ),


def downgrade():
    op.drop_column("annotated_docs", "failed_validation_pages")
    op.drop_column("annotated_docs", "task_id")
