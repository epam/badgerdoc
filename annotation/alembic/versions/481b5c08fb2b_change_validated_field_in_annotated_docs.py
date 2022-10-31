"""Change validated field in annotated_docs

Revision ID: 481b5c08fb2b
Revises: 4cd10ac49cc2
Create Date: 2021-12-13 17:50:11.881829

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "481b5c08fb2b"
down_revision = "4cd10ac49cc2"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("annotated_docs", "validated", server_default="{}")


def downgrade():
    op.alter_column("annotated_docs", "validated", server_default=None)
