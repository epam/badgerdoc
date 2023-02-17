"""empty message

Revision ID: 29f072fb5c9c
Revises: 08ad5deb23eb
Create Date: 2022-04-04 10:27:38.546029

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "29f072fb5c9c"
down_revision = "08ad5deb23eb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        op.f("ix_execution_step_task_id"),
        "execution_step",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pipeline_execution_task_job_id"),
        "pipeline_execution_task",
        ["job_id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f("ix_pipeline_execution_task_job_id"),
        table_name="pipeline_execution_task",
    )
    op.drop_index(op.f("ix_execution_step_task_id"), table_name="execution_step")
    # ### end Alembic commands ###
