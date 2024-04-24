"""document_link category enum type

Revision ID: f1a58d769aa2
Revises: e56cb55fde06
Create Date: 2022-12-26 21:13:11.571188

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f1a58d769aa2"
down_revision = "e56cb55fde06"
branch_labels = None
depends_on = None

enum_name = "document_link"
enum_type = "categorytypeschema"


def upgrade():
    op.execute(f"ALTER TYPE {enum_type} ADD VALUE '{enum_name}'")


def downgrade():
    sql = f"""DELETE FROM pg_enum
            WHERE enumlabel = '{enum_name}'
            AND enumtypid = (
              SELECT oid FROM pg_type WHERE typname = '{enum_type}'
            )"""
    op.execute(sql)
