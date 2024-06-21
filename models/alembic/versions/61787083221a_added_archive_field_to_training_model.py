"""Added archive field to training model

Revision ID: 61787083221a
Revises: 5c3092bc3517
Create Date: 2022-04-26 11:32:45.849502

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "61787083221a"
down_revision = "5c3092bc3517"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "training", sa.Column("key_archive", sa.String(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("training", "key_archive")
    # ### end Alembic commands ###