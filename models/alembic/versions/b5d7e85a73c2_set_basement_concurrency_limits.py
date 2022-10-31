"""hard limits

Revision ID: b5d7e85a73c2
Revises: 0c3e4fd362de
Create Date: 2022-05-06 17:06:27.746823

"""
from json import dumps

from alembic import op

# revision identifiers, used by Alembic.
revision = "b5d7e85a73c2"
down_revision = "0c3e4fd362de"
branch_labels = None
depends_on = None


def upgrade():
    default_limits = {
        "pod_cpu": "1000m",
        "pod_memory": "4Gi",
        "concurrency_limit": 1,
    }
    ternary_classifier_limits = {
        "pod_cpu": "1000m",
        "pod_memory": "2Gi",
        "concurrency_limit": 1,
    }
    dod_limits = {
        "pod_cpu": "1000m",
        "pod_memory": "4Gi",
        "concurrency_limit": 1,
    }

    table_extractor_limits = {
        "pod_cpu": "1000m",
        "pod_memory": "6Gi",
        "concurrency_limit": 1,
    }

    op.execute(f"UPDATE basement SET limits = '{dumps(default_limits)}'")
    op.execute(
        f"UPDATE basement SET limits = '{dumps(dod_limits)}' "
        "WHERE id LIKE '%dod%'"
    )
    op.execute(
        f"UPDATE basement SET limits = '{dumps(table_extractor_limits)}' "
        "WHERE id LIKE '%table_extractor%'"
    )
    op.execute(
        f"UPDATE basement SET limits = '{dumps(ternary_classifier_limits)}' "
        "WHERE id LIKE '%ternary_classifier%'"
    )


def downgrade():
    default_limits = {
        "pod_cpu": "1000m",
        "pod_memory": "4Gi",
    }
    ternary_classifier_limits = {
        "pod_cpu": "1000m",
        "pod_memory": "2Gi",
    }
    dod_limits = {
        "pod_cpu": "1000m",
        "pod_memory": "4Gi",
    }

    table_extractor_limits = {
        "pod_cpu": "1000m",
        "pod_memory": "6Gi",
    }

    op.execute(f"UPDATE basement SET limits = '{dumps(default_limits)}'")
    op.execute(
        f"UPDATE basement SET limits = '{dumps(dod_limits)}' "
        "WHERE id LIKE '%dod%'"
    )
    op.execute(
        f"UPDATE basement SET limits = '{dumps(table_extractor_limits)}' "
        "WHERE id LIKE '%table_extractor%'"
    )
    op.execute(
        f"UPDATE basement SET limits = '{dumps(ternary_classifier_limits)}' "
        "WHERE id LIKE '%ternary_classifier%'"
    )
