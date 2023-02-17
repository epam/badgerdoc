"""fix default type to inference

Revision ID: 0ab5e65cf34b
Revises: 8a589dda3869
Create Date: 2022-04-26 19:37:27.263471

"""
import sqlalchemy as sa
from sqlalchemy import orm

from alembic import op
from pipelines.db import models

# revision identifiers, used by Alembic.
revision = "0ab5e65cf34b"
down_revision = "8a589dda3869"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = orm.Session(bind=op.get_bind())
    session.query(models.Pipeline).filter(
        models.Pipeline.type.is_(None)
    ).update({models.Pipeline.type: "inference"}, synchronize_session="fetch")
    session.commit()
    session.close()


def downgrade() -> None:
    pass
