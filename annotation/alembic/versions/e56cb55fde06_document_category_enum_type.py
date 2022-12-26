"""document category enum type

Revision ID: e56cb55fde06
Revises: 71095b8e6343
Create Date: 2022-12-26 16:18:31.868955

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "e56cb55fde06"
down_revision = "71095b8e6343"
branch_labels = None
depends_on = None

enum_name = "document"
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
