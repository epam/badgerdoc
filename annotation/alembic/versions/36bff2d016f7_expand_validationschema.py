"""Expand ValidationSchema

Revision ID: 36bff2d016f7
Revises: c06c594c7435
Create Date: 2021-12-28 15:09:23.826747

"""
from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "36bff2d016f7"
down_revision = "c06c594c7435"
branch_labels = None
depends_on = None


DOCS_TASK_ID_FK = "annotated_docs_task_id_fkey"

JOB_ANNOTATOR_JOB_ID_FK = "association_job_annotator_job_id_fkey"
JOB_ANNOTATOR_USER_ID_FK = "association_job_annotator_user_id_fkey"

JOB_OWNER_JOB_ID_FK = "association_job_owner_job_id_fkey"
JOB_OWNER_USER_ID_FK = "association_job_owner_user_id_fkey"

JOB_VALIDATOR_JOB_ID_FK = "association_job_validator_job_id_fkey"
JOB_VALIDATOR_USER_ID_FK = "association_job_validator_user_id_fkey"

TASKS_JOB_ID_FK = "tasks_job_id_fkey"


def upgrade():
    """
    Add `cascade` delete option on fk and
    add new job type - validation_only.
    """
    op.drop_constraint(DOCS_TASK_ID_FK, "annotated_docs", type_="foreignkey")
    op.create_foreign_key(
        DOCS_TASK_ID_FK,
        "annotated_docs",
        "tasks",
        ["task_id"],
        ["id"],
        ondelete="cascade",
    )

    op.drop_constraint(
        JOB_ANNOTATOR_USER_ID_FK,
        "association_job_annotator",
        type_="foreignkey",
    )
    op.drop_constraint(
        JOB_ANNOTATOR_JOB_ID_FK,
        "association_job_annotator",
        type_="foreignkey",
    )
    op.create_foreign_key(
        JOB_ANNOTATOR_USER_ID_FK,
        "association_job_annotator",
        "jobs",
        ["job_id"],
        ["job_id"],
        ondelete="cascade",
    )
    op.create_foreign_key(
        JOB_ANNOTATOR_JOB_ID_FK,
        "association_job_annotator",
        "users",
        ["user_id"],
        ["user_id"],
        ondelete="cascade",
    )

    op.drop_constraint(
        JOB_OWNER_JOB_ID_FK, "association_job_owner", type_="foreignkey"
    )
    op.drop_constraint(
        JOB_OWNER_USER_ID_FK, "association_job_owner", type_="foreignkey"
    )
    op.create_foreign_key(
        JOB_OWNER_JOB_ID_FK,
        "association_job_owner",
        "jobs",
        ["job_id"],
        ["job_id"],
        ondelete="cascade",
    )
    op.create_foreign_key(
        JOB_OWNER_USER_ID_FK,
        "association_job_owner",
        "users",
        ["user_id"],
        ["user_id"],
        ondelete="cascade",
    )

    op.drop_constraint(
        JOB_VALIDATOR_JOB_ID_FK,
        "association_job_validator",
        type_="foreignkey",
    )
    op.drop_constraint(
        JOB_VALIDATOR_USER_ID_FK,
        "association_job_validator",
        type_="foreignkey",
    )
    op.create_foreign_key(
        JOB_VALIDATOR_JOB_ID_FK,
        "association_job_validator",
        "jobs",
        ["job_id"],
        ["job_id"],
        ondelete="cascade",
    )
    op.create_foreign_key(
        JOB_VALIDATOR_USER_ID_FK,
        "association_job_validator",
        "users",
        ["user_id"],
        ["user_id"],
        ondelete="cascade",
    )

    op.drop_constraint(TASKS_JOB_ID_FK, "tasks", type_="foreignkey")
    op.create_foreign_key(
        TASKS_JOB_ID_FK,
        "tasks",
        "jobs",
        ["job_id"],
        ["job_id"],
        ondelete="cascade",
    )

    op.execute(
        "ALTER TYPE validation_type ADD VALUE IF NOT EXISTS 'validation_only'"
    )


class ValidationSchema(str, Enum):
    cross = "cross"
    hierarchical = "hierarchical"


def downgrade():
    """
    Remove validation_only job type and
    rollback fk constraints
    """
    op.alter_column(
        "jobs", "validation_type", type_=sa.VARCHAR(), server_default=None
    )
    op.execute("DROP TYPE validation_type;")

    op.execute("DELETE FROM jobs " "WHERE validation_type = 'validation_only'")
    validation_type = postgresql.ENUM(ValidationSchema, name="validation_type")
    validation_type.create(op.get_bind(), checkfirst=True)
    op.alter_column(
        "jobs",
        "validation_type",
        type_=validation_type,
        server_default=ValidationSchema.cross.name,
        postgresql_using="validation_type::validation_type",
    )

    op.drop_constraint(TASKS_JOB_ID_FK, "tasks", type_="foreignkey")
    op.create_foreign_key(
        TASKS_JOB_ID_FK, "tasks", "jobs", ["job_id"], ["job_id"]
    )

    op.drop_constraint(
        JOB_VALIDATOR_USER_ID_FK,
        "association_job_validator",
        type_="foreignkey",
    )
    op.drop_constraint(
        JOB_VALIDATOR_JOB_ID_FK,
        "association_job_validator",
        type_="foreignkey",
    )
    op.create_foreign_key(
        JOB_VALIDATOR_USER_ID_FK,
        "association_job_validator",
        "users",
        ["user_id"],
        ["user_id"],
    )
    op.create_foreign_key(
        JOB_VALIDATOR_JOB_ID_FK,
        "association_job_validator",
        "jobs",
        ["job_id"],
        ["job_id"],
    )

    op.drop_constraint(
        JOB_OWNER_USER_ID_FK, "association_job_owner", type_="foreignkey"
    )
    op.drop_constraint(
        JOB_OWNER_JOB_ID_FK, "association_job_owner", type_="foreignkey"
    )
    op.create_foreign_key(
        JOB_OWNER_USER_ID_FK,
        "association_job_owner",
        "users",
        ["user_id"],
        ["user_id"],
    )
    op.create_foreign_key(
        JOB_OWNER_JOB_ID_FK,
        "association_job_owner",
        "jobs",
        ["job_id"],
        ["job_id"],
    )

    op.drop_constraint(
        JOB_ANNOTATOR_USER_ID_FK,
        "association_job_annotator",
        type_="foreignkey",
    )
    op.drop_constraint(
        JOB_ANNOTATOR_JOB_ID_FK,
        "association_job_annotator",
        type_="foreignkey",
    )
    op.create_foreign_key(
        JOB_ANNOTATOR_USER_ID_FK,
        "association_job_annotator",
        "users",
        ["user_id"],
        ["user_id"],
    )
    op.create_foreign_key(
        JOB_ANNOTATOR_JOB_ID_FK,
        "association_job_annotator",
        "jobs",
        ["job_id"],
        ["job_id"],
    )

    op.drop_constraint(DOCS_TASK_ID_FK, "annotated_docs", type_="foreignkey")
    op.create_foreign_key(
        DOCS_TASK_ID_FK, "annotated_docs", "tasks", ["task_id"], ["id"]
    )
