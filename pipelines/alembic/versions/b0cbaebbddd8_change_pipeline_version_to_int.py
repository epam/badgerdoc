"""change pipeline version to int

Revision ID: b0cbaebbddd8
Revises: 0ab5e65cf34b
Create Date: 2022-04-27 18:30:19.533396

"""
import sqlalchemy as sa
from sqlalchemy import orm

from alembic import op
from src.db import models

# revision identifiers, used by Alembic.
revision = "b0cbaebbddd8"
down_revision = "0ab5e65cf34b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = orm.Session(bind=op.get_bind())
    session.query(models.Pipeline).update(
        {models.Pipeline.version: None},
        synchronize_session="fetch",
    )
    session.commit()
    session.close()

    session = orm.Session(bind=op.get_bind())
    rows = (
        session.query(models.Pipeline)
        .options(orm.load_only("id", "meta"))
        .all()
    )
    for row in rows:
        new_meta = dict(row.meta)
        new_meta["version"] = 1
        row.meta = new_meta
    session.commit()
    session.close()

    op.alter_column(
        "pipeline",
        "version",
        type_=sa.INTEGER,
        existing_type=sa.String,
        postgresql_using="version::integer",
    )

    session = orm.Session(bind=op.get_bind())
    session.query(models.Pipeline).update(
        {models.Pipeline.version: 1},
        synchronize_session="fetch",
    )
    session.commit()
    session.close()


def downgrade() -> None:
    session = orm.Session(bind=op.get_bind())
    session.query(models.Pipeline).update(
        {models.Pipeline.version: None},
        synchronize_session="fetch",
    )
    session.commit()
    session.close()

    op.alter_column(
        "pipeline",
        "version",
        type_=sa.String,
        existing_type=sa.INTEGER,
        postgresql_using="version::varchar",
    )

    session = orm.Session(bind=op.get_bind())
    session.query(models.Pipeline).update(
        {models.Pipeline.version: "v1"},
        synchronize_session="fetch",
    )
    session.commit()
    session.close()

    session = orm.Session(bind=op.get_bind())
    rows = (
        session.query(models.Pipeline)
        .options(orm.load_only("id", "meta"))
        .all()
    )
    for row in rows:
        new_meta = dict(row.meta)
        new_meta["version"] = "v1"
        row.meta = new_meta
    session.commit()
    session.close()
