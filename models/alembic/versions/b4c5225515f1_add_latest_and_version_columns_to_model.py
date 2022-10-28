"""Add latest and version columns to model

Revision ID: b4c5225515f1
Revises: 5c3092bc3517
Create Date: 2022-05-11 11:44:11.235894

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b4c5225515f1"
down_revision = "61787083221a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "model",
        sa.Column(
            "latest", sa.Boolean(), nullable=False, server_default="True"
        ),
    )
    op.alter_column("model", "latest", server_default=None)

    op.add_column(
        "model",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.alter_column("model", "version", server_default=None)

    op.drop_constraint("model_pkey", "model", type_="primary")
    op.create_primary_key("model_pkey", "model", ["id", "version"])


def downgrade():
    # leave rows only with latest eq True
    op.execute("DELETE FROM model WHERE NOT latest")
    op.drop_constraint("model_pkey", "model", type_="primary")
    op.create_primary_key("model_pkey", "model", ["id"])

    op.drop_column("model", "version")
    op.drop_column("model", "latest")
