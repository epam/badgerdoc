"""change webhook to str

Revision ID: 0a53c56436d0
Revises: 764961499e2b
Create Date: 2022-05-17 16:28:24.508699

"""
import sqlalchemy as sa
from sqlalchemy import orm

from alembic import op
from src.db import models

# revision identifiers, used by Alembic.
revision = "0a53c56436d0"
down_revision = "764961499e2b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = orm.Session(bind=op.get_bind())
    session.query(models.PipelineExecutionTask).update(
        {models.PipelineExecutionTask.webhook: None},
        synchronize_session="fetch",
    )
    session.commit()
    session.close()

    op.alter_column(
        "pipeline_execution_task",
        "webhook",
        type_=sa.String,
        existing_type=sa.JSON,
        postgresql_using="webhook::varchar",
    )


def downgrade() -> None:
    session = orm.Session(bind=op.get_bind())
    session.query(models.PipelineExecutionTask).update(
        {models.PipelineExecutionTask.webhook: None},
        synchronize_session="fetch",
    )
    session.commit()
    session.close()

    op.alter_column(
        "pipeline_execution_task",
        "webhook",
        type_=sa.JSON,
        existing_type=sa.String,
        postgresql_using="webhook::json",
    )
