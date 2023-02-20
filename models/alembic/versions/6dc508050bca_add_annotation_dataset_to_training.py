"""add dataset_url to training instance

Revision ID: 6dc508050bca
Revises: b5d7e85a73c2
Create Date: 2022-05-26 15:51:37.509932

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6dc508050bca"
down_revision = "b5d7e85a73c2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "training",
        sa.Column("key_annotation_dataset", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("training", "key_annotation_dataset")
