"""Change pages field in annotated_docs

Revision ID: d31fc5f752ac
Revises: 481b5c08fb2b
Create Date: 2021-12-14 13:40:29.182661

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d31fc5f752ac"
down_revision = "481b5c08fb2b"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("annotated_docs", "pages", server_default="{}")


def downgrade():
    op.alter_column("annotated_docs", "pages", server_default=None)
