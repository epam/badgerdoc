"""add extensive_coverage param

Revision ID: f60dd492b17f
Revises: b4afb5ae8923
Create Date: 2022-12-09 13:10:42.668902

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f60dd492b17f"
down_revision = "b4afb5ae8923"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "job", sa.Column("extensive_coverage", sa.Integer(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("job", "extensive_coverage")
    # ### end Alembic commands ###
