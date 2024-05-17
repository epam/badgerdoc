"""add association_taxonomy_category

Revision ID: 48dc50decbed
Revises: bdea8a93cafe
Create Date: 2022-12-02 15:04:55.726594

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "48dc50decbed"
down_revision = "bdea8a93cafe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "association_taxonomy_category",
        sa.Column("taxonomy_id", sa.VARCHAR(), nullable=False),
        sa.Column("taxonomy_version", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.VARCHAR(), nullable=False),
        sa.ForeignKeyConstraint(
            ["taxonomy_id", "taxonomy_version"],
            ["taxonomy.id", "taxonomy.version"],
        ),
        sa.PrimaryKeyConstraint(
            "taxonomy_id", "taxonomy_version", "category_id"
        ),
    )
    op.drop_column("taxonomy", "category_id")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "taxonomy",
        sa.Column(
            "category_id", sa.VARCHAR(), autoincrement=False, nullable=False
        ),
    )
    op.drop_table("association_taxonomy_category")
    # ### end Alembic commands ###
