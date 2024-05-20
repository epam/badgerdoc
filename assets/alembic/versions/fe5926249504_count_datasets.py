"""count_datasets

Revision ID: fe5926249504
Revises:
Create Date: 2021-10-28 18:28:20.687405

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import Session

from assets.db.models import Association, Datasets, FileObject

# revision identifiers, used by Alembic.
revision = "fe5926249504"
down_revision = "afa33cc83d57"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("datasets", sa.Column("count", sa.Integer(), nullable=True))
    session = Session(bind=op.get_bind())
    query = session.query(Datasets).filter(Datasets.count.is_(None))
    ids = [row.id for row in query]
    for ds_id in ids:
        current_count = (
            session.query(FileObject)
            .join(Association)
            .filter(Association.dataset_id == ds_id)
            .count()
        )
        session.query(Datasets).filter(Datasets.id == ds_id).update(
            {Datasets.count: current_count}
        )
        session.commit()
    session.close()


def downgrade() -> None:
    op.drop_column("datasets", "count")
