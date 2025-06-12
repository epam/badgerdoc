"""Create Veeva PM tables

Revision ID: fe000649d40d
Revises: 
Create Date: 2025-06-06 12:10:54.866515

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "fe000649d40d"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create veeva_pm_configurations table
    op.create_table(
        "veeva_pm_configurations",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("tenant", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("sync_type", sa.String(), nullable=False),
        sa.Column("protocol", sa.String(), nullable=False),
        sa.Column("veeva_pm_host", sa.String(), nullable=False),
        sa.Column("veeva_pm_login", sa.String(), nullable=False),
        sa.Column("veeva_pm_password", sa.String(), nullable=False),
        sa.Column("veeva_pm_vql", sa.String(), nullable=True),
        sa.Column("soft_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create veeva_pm_synchronization_runs table
    op.create_table(
        "veeva_pm_synchronization_runs",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("configuration_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "queued",
                "in_progress",
                "finished",
                "timed_out",
                name="veeva_pm_synchronization_status_enum",
                create_type=True,
            ),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["configuration_id"], ["veeva_pm_configurations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create veeva_pm_document table
    op.create_table(
        "veeva_pm_document",
        sa.Column("synchronization_id", sa.Integer(), nullable=False),
        sa.Column("veeva_document_id", sa.String(), nullable=False),
        sa.Column("badgerdoc_file_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("source_file", sa.String(), nullable=True),
        sa.Column("viewable_rendition", sa.String(), nullable=True),
        sa.Column("checksum", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["synchronization_id"],
            ["veeva_pm_synchronization_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("veeva_document_id"),
    )

    # Create veeva_pm_metadata_version table
    op.create_table(
        "veeva_pm_metadata_version",
        sa.Column("veeva_document_id", sa.String(), nullable=False),
        sa.Column("major_version", sa.Integer(), nullable=False),
        sa.Column("minor_version", sa.Integer(), nullable=False),
        sa.Column("version_modified_date", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("synchronization_id", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(
            ["veeva_document_id"],
            ["veeva_pm_document.veeva_document_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["synchronization_id"],
            ["veeva_pm_synchronization_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "veeva_document_id",
            "major_version",
            "minor_version",
            "version_modified_date",
        ),
    )

    # Create veeva_pm_synchronization_log table
    op.create_table(
        "veeva_pm_synchronization_log",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("synchronization_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("message", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["synchronization_id"],
            ["veeva_pm_synchronization_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create veeva_pm_mappings table
    op.create_table(
        "veeva_pm_mappings",
        sa.Column("veeva_mapping_id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("synchronization_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["synchronization_id"],
            ["veeva_pm_synchronization_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("veeva_mapping_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the tables in the correct order (respecting foreign key constraints)
    op.drop_table("veeva_pm_mappings")
    op.drop_table("veeva_pm_synchronization_log")
    op.drop_table("veeva_pm_metadata_version")
    op.drop_table("veeva_pm_document")
    op.drop_table("veeva_pm_synchronization_runs")
    op.drop_table("veeva_pm_configurations")

    op.execute("DROP TYPE IF EXISTS veeva_pm_synchronization_status_enum")
