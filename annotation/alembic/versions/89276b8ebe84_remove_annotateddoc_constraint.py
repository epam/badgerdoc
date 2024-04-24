"""Remove AnnotatedDoc constraint

Revision ID: 89276b8ebe84
Revises: 416952520dc1
Create Date: 2022-04-01 15:43:54.112660

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "89276b8ebe84"
down_revision = "416952520dc1"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("annotated_docs_check", "annotated_docs", type_="check")
    op.drop_constraint(
        "annotated_docs_task_id_fkey", "annotated_docs", type_="foreignkey"
    )
    op.drop_constraint(
        "annotated_docs_user_fkey", "annotated_docs", type_="foreignkey"
    )
    op.create_foreign_key(
        None,
        "annotated_docs",
        "users",
        ["user"],
        ["user_id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        None,
        "annotated_docs",
        "tasks",
        ["task_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.execute(
        'DELETE FROM annotated_docs WHERE "user" IS NULL AND pipeline IS NULL'
    )
    op.create_check_constraint(
        "annotated_docs_check",
        "annotated_docs",
        '("user" IS NULL AND pipeline IS NOT NULL) OR '
        '("user" IS NOT NULL AND pipeline IS NULL)',
    )
    op.drop_constraint(
        "annotated_docs_user_fkey", "annotated_docs", type_="foreignkey"
    )
    op.drop_constraint(
        "annotated_docs_task_id_fkey", "annotated_docs", type_="foreignkey"
    )
    op.create_foreign_key(
        "annotated_docs_user_fkey",
        "annotated_docs",
        "users",
        ["user"],
        ["user_id"],
    )
    op.create_foreign_key(
        "annotated_docs_task_id_fkey",
        "annotated_docs",
        "tasks",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )
