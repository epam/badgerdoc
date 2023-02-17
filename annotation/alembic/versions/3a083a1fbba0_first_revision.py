"""First revision

Revision ID: 3a083a1fbba0
Revises:
Create Date: 2021-11-19 12:00:29.218594

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

from alembic import op

# revision identifiers, used by Alembic.
revision = "3a083a1fbba0"
down_revision = None
branch_labels = None
depends_on = None


def get_tables():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    return inspector.get_table_names()


def upgrade():
    tables = get_tables()  # List of existing tables in database
    if "annotators" not in tables:
        op.create_table(
            "annotators",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("default_load", sa.INTEGER(), nullable=False),
            sa.PrimaryKeyConstraint("user_id"),
        )  # Here and below this 'if' condition creates tables only for new db
    if "categories" not in tables:
        op.create_table(
            "categories",
            sa.Column("id", sa.INTEGER(), nullable=False),
            sa.Column("tenant", sa.VARCHAR(), nullable=True),
            sa.Column("name", sa.VARCHAR(), nullable=False),
            sa.Column("parent", sa.INTEGER(), nullable=True),
            sa.Column(
                "metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column("is_link", sa.BOOLEAN(), nullable=False),
            sa.ForeignKeyConstraint(["parent"], ["categories.id"], ondelete="cascade"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_check_constraint(
            "is_not_self_parent", "categories", "id != parent"
        )  # Add this constraint manually - not autogenerated by alembic
        op.create_index(
            op.f("ix_categories_is_link"),
            "categories",
            ["is_link"],
            unique=False,
        )
        op.create_index(
            op.f("ix_categories_parent"),
            "categories",
            ["parent"],
            unique=False,
        )
    if "jobs" not in tables:
        op.create_table(
            "jobs",
            sa.Column("job_id", sa.INTEGER(), nullable=False),
            sa.Column("is_auto_distribution", sa.BOOLEAN(), nullable=False),
            sa.Column("callback_url", sa.VARCHAR(), nullable=False),
            sa.Column("deadline", sa.TIMESTAMP(), nullable=True),
            sa.PrimaryKeyConstraint("job_id"),
        )
    if "annotated_docs" not in tables:
        op.create_table(
            "annotated_docs",
            sa.Column("revision", sa.VARCHAR(), nullable=False),
            sa.Column("user", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("pipeline", sa.INTEGER(), nullable=True),
            sa.Column(
                "date",
                sa.TIMESTAMP(),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("file_id", sa.INTEGER(), nullable=False),
            sa.Column("job_id", sa.INTEGER(), nullable=False),
            sa.Column("pages", postgresql.JSON(astext_type=sa.Text()), nullable=False),
            sa.Column("validated", postgresql.ARRAY(sa.INTEGER()), nullable=False),
            sa.Column("tenant", sa.VARCHAR(), nullable=False),
            sa.CheckConstraint(
                '("user" IS NULL AND pipeline IS NOT NULL) OR '
                '("user" IS NOT NULL AND pipeline IS NULL)',
            ),
            sa.ForeignKeyConstraint(
                ["user"],
                ["annotators.user_id"],
            ),
            sa.PrimaryKeyConstraint("revision", "file_id", "job_id"),
        )
    if "association_job_annotator" not in tables:
        op.create_table(
            "association_job_annotator",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("job_id", sa.INTEGER(), nullable=False),
            sa.ForeignKeyConstraint(
                ["job_id"],
                ["jobs.job_id"],
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["annotators.user_id"],
            ),
            sa.PrimaryKeyConstraint("user_id", "job_id"),
        )
    if "association_jobs_categories" not in tables:
        op.create_table(
            "association_jobs_categories",
            sa.Column("category_id", sa.INTEGER(), nullable=False),
            sa.Column("job_id", sa.INTEGER(), nullable=False),
            sa.ForeignKeyConstraint(
                ["category_id"],
                ["categories.id"],
            ),
            sa.ForeignKeyConstraint(
                ["job_id"],
                ["jobs.job_id"],
            ),
            sa.PrimaryKeyConstraint("category_id", "job_id"),
        )
    if "files" not in tables:
        op.create_table(
            "files",
            sa.Column("file_id", sa.INTEGER(), nullable=False),
            sa.Column("tenant", sa.VARCHAR(), nullable=False),
            sa.Column("job_id", sa.INTEGER(), nullable=False),
            sa.Column("pages_number", sa.INTEGER(), nullable=False),
            sa.ForeignKeyConstraint(
                ["job_id"],
                ["jobs.job_id"],
            ),
            sa.PrimaryKeyConstraint("file_id", "job_id"),
        )
    if "tasks" not in tables:
        op.create_table(
            "tasks",
            sa.Column("id", sa.INTEGER(), nullable=False),
            sa.Column("file_id", sa.INTEGER(), nullable=False),
            sa.Column("pages", postgresql.ARRAY(sa.INTEGER()), nullable=False),
            sa.Column("job_id", sa.INTEGER(), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("is_validation", sa.BOOLEAN(), nullable=False),
            sa.Column(
                "status",
                postgresql.ENUM(
                    "pending",
                    "ready",
                    "in_progress",
                    "finished",
                    name="taskstatusenumschema",
                ),
                nullable=False,
            ),
            sa.Column("deadline", sa.TIMESTAMP(), nullable=True),
            sa.ForeignKeyConstraint(
                ["job_id"],
                ["jobs.job_id"],
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["annotators.user_id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
    # ### end Alembic commands ###


def downgrade():
    op.drop_table("tasks")
    op.drop_table("files")
    op.drop_table("association_jobs_categories")
    op.drop_table("association_job_annotator")
    op.drop_table("annotated_docs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_categories_parent"), table_name="categories")
    op.drop_index(op.f("ix_categories_is_link"), table_name="categories")
    op.drop_table("categories")
    op.drop_table("annotators")
    op.execute("DROP TYPE taskstatusenumschema;")
    # ### end Alembic commands ###
