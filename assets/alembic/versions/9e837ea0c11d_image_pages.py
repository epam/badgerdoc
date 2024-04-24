"""image_pages

Revision ID: 9e837ea0c11d
Revises: 0f6c859c1d1c
Create Date: 2022-02-14 17:36:57.252191

"""

from assets.db.models import FileObject
from sqlalchemy.orm import Session

from alembic import op

# revision identifiers, used by Alembic.

revision = "9e837ea0c11d"
down_revision = "0f6c859c1d1c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    session.query(FileObject).filter(
        FileObject.pages.is_(None), FileObject.content_type.like("image/%")
    ).update({FileObject.pages: 1}, synchronize_session="fetch")
    session.commit()
    session.close()


def downgrade() -> None:
    pass
