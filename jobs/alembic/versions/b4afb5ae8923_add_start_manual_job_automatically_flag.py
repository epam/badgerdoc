"""Add start_manual_job_automatically flag

Revision ID: b4afb5ae8923
Revises: 86f432539475
Create Date: 2022-03-17 20:22:30.242625

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b4afb5ae8923"
down_revision = "86f432539475"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "job",
        sa.Column(
            "start_manual_job_automatically", sa.Boolean(), nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("job", "start_manual_job_automatically")
    # ### end Alembic commands ###
