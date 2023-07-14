"""alter_categories_id_from_INTEGER_to_VARCHAR

Revision ID: 2b3ed53127ea
Revises: d31fc5f752ac
Create Date: 2021-12-14 08:54:04.200572

"""
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

from alembic import op

# revision identifiers, used by Alembic.
revision = "2b3ed53127ea"
down_revision = "d31fc5f752ac"
branch_labels = None
depends_on = None

categories_id_seq = sa.Sequence("categories_id_seq")


def upgrade():
    op.drop_constraint(
        "categories_parent_fkey", "categories", type_="foreignkey"
    )
    op.drop_constraint(
        "association_jobs_categories_category_id_fkey",
        "association_jobs_categories",
        type_="foreignkey",
    )
    op.add_column(
        "categories",
        sa.Column(
            "parent_temp",
            sa.VARCHAR(),
            nullable=True,
        ),
    )
    op.add_column(
        "categories",
        sa.Column(
            "id_temp",
            sa.VARCHAR(),
            sa.Sequence("categories_id_seq"),
            nullable=True,
            primary_key=True,
        ),
    )
    op.add_column(
        "association_jobs_categories",
        sa.Column(
            "category_id_temp",
            sa.VARCHAR(),
            nullable=True,
        ),
    )
    op.execute("UPDATE categories SET parent_temp = CAST(parent AS varchar)")
    op.execute("UPDATE categories SET id_temp = CAST(id AS varchar)")
    op.execute(
        "UPDATE association_jobs_categories "
        "SET category_id_temp = CAST(category_id AS varchar)"
    )
    op.drop_column("categories", "parent")
    op.drop_column("categories", "id")
    op.drop_column("association_jobs_categories", "category_id")
    op.create_primary_key("pk_categories", "categories", ["id_temp"])
    op.create_foreign_key(
        "categories_parent_fkey",
        "categories",
        "categories",
        ["parent_temp"],
        ["id_temp"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "association_jobs_categories_category_id_fkey",
        "association_jobs_categories",
        "categories",
        ["category_id_temp"],
        ["id_temp"],
    )
    op.alter_column(
        "categories",
        "parent_temp",
        new_column_name="parent",
        server_default="null",
    )
    op.alter_column(
        "categories", "id_temp", new_column_name="id", nullable=False
    )
    op.alter_column(
        "association_jobs_categories",
        "category_id_temp",
        new_column_name="category_id",
        nullable=False,
    )
    op.create_check_constraint(
        "is_not_self_parent", "categories", "id != parent"
    )
    op.create_index(
        op.f("ix_categories_parent"),
        "categories",
        ["parent"],
        unique=False,
    )


def check_exist_sequence():
    conn = op.get_bind()
    sequences = conn.execute("SELECT * FROM information_schema.sequences")
    return "categories_id_seq" in [sequence[2] for sequence in sequences]


def clear_tables():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = [
        data[0] for data in inspector.get_sorted_table_and_fkc_names()[-2::-1]
    ]
    tables.remove("alembic_revision_annotation")
    for table in tables:
        conn.execute(f"DELETE FROM {table}")


def downgrade():
    clear_tables()
    if not check_exist_sequence():
        op.execute(sa.schema.CreateSequence(categories_id_seq))
    op.drop_constraint(
        "categories_parent_fkey", "categories", type_="foreignkey"
    )
    op.drop_constraint(
        "association_jobs_categories_category_id_fkey",
        "association_jobs_categories",
        type_="foreignkey",
    )
    op.add_column(
        "categories",
        sa.Column(
            "parent_temp",
            sa.INTEGER(),
            nullable=True,
        ),
    )
    op.add_column(
        "categories",
        sa.Column(
            "id_temp",
            sa.INTEGER(),
            categories_id_seq,
            nullable=True,
            primary_key=True,
            server_default=categories_id_seq.next_value(),
        ),
    ),
    op.add_column(
        "association_jobs_categories",
        sa.Column(
            "category_id_temp",
            sa.INTEGER(),
            nullable=True,
        ),
    )
    op.drop_column("categories", "parent")
    op.drop_column("categories", "id")
    op.drop_column("association_jobs_categories", "category_id")
    op.create_primary_key("pk_categories", "categories", ["id_temp"])
    op.create_foreign_key(
        "categories_parent_fkey",
        "categories",
        "categories",
        ["parent_temp"],
        ["id_temp"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "association_jobs_categories_category_id_fkey",
        "association_jobs_categories",
        "categories",
        ["category_id_temp"],
        ["id_temp"],
    )
    op.alter_column(
        "categories",
        "parent_temp",
        new_column_name="parent",
    )
    op.alter_column(
        "categories", "id_temp", new_column_name="id", nullable=False
    )
    op.alter_column(
        "association_jobs_categories",
        "category_id_temp",
        new_column_name="category_id",
        nullable=False,
    )
    op.create_check_constraint(
        "is_not_self_parent", "categories", "id != parent"
    )
    op.create_index(
        op.f("ix_categories_parent"),
        "categories",
        ["parent"],
        unique=False,
    )
    # ### end Alembic commands ###
