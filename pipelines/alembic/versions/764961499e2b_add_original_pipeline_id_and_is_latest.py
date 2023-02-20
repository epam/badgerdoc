"""add 'original_pipeline_id' and 'is_latest' to pipelines

Revision ID: 764961499e2b
Revises: b0cbaebbddd8
Create Date: 2022-04-28 15:21:32.025260

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import orm

from pipelines.db import models

# revision identifiers, used by Alembic.
revision = "764961499e2b"
down_revision = "b0cbaebbddd8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pipeline",
        sa.Column("original_pipeline_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "pipeline", sa.Column("is_latest", sa.Boolean(), nullable=True)
    )

    session = orm.Session(bind=op.get_bind())
    rows = (
        session.query(models.Pipeline)
        .filter(models.Pipeline.original_pipeline_id.is_(None))
        .options(orm.load_only("id", "original_pipeline_id", "is_latest"))
        .all()
    )
    for row in rows:
        row.original_pipeline_id = row.id
        row.is_latest = True
    session.commit()
    session.close()


def downgrade() -> None:
    op.drop_column("pipeline", "is_latest")
    op.drop_column("pipeline", "original_pipeline_id")
