"""add type, description and summary to pipeline

Revision ID: 8a589dda3869
Revises: df42f45f4ddf
Create Date: 2022-04-26 19:13:09.698256

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8a589dda3869"
down_revision = "df42f45f4ddf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "pipeline", sa.Column("type", sa.String(length=30), nullable=True)
    )
    op.add_column(
        "pipeline", sa.Column("description", sa.Text(), nullable=True)
    )
    op.add_column("pipeline", sa.Column("summary", sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("pipeline", "summary")
    op.drop_column("pipeline", "description")
    op.drop_column("pipeline", "type")
    # ### end Alembic commands ###