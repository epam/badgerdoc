"""pod cpu limits change

Revision ID: 8fd15e9edd28
Revises: 826680104247
Create Date: 2022-04-22 17:04:04.015869

"""
from json import dumps

from alembic import op

# revision identifiers, used by Alembic.
revision = "8fd15e9edd28"
down_revision = "826680104247"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
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
        f"UPDATE basement SET limits = "
        f"'{dumps(dod_limits)}' WHERE id LIKE '%dod%'"
    )
    op.execute(
        f"UPDATE basement SET limits = "
        f"'{dumps(table_extractor_limits)}' "
        f"WHERE id LIKE '%table_extractor%'"
    )
    op.execute(
        f"UPDATE basement SET limits = "
        f"'{dumps(ternary_classifier_limits)}' "
        f"WHERE id LIKE '%ternary_classifier%'"
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    default_limits = {
        "pod_cpu": "2000m",
        "pod_memory": "4Gi",
    }
    ternary_classifier_limits = {
        "pod_cpu": "2000m",
        "pod_memory": "2Gi",
    }
    dod_limits = {
        "pod_cpu": "2000m",
        "pod_memory": "4Gi",
    }

    table_extractor_limits = {
        "pod_cpu": "2000m",
        "pod_memory": "6Gi",
    }

    op.execute(f"UPDATE basement SET limits = '{dumps(default_limits)}'")
    op.execute(
        f"UPDATE basement SET limits ="
        f" '{dumps(dod_limits)}' WHERE id LIKE '%dod%'"
    )
    op.execute(
        f"UPDATE basement SET limits ="
        f" '{dumps(table_extractor_limits)}'"
        f" WHERE id LIKE '%table_extractor%'"
    )
    op.execute(
        f"UPDATE basement SET limits ="
        f" '{dumps(ternary_classifier_limits)}'"
        f" WHERE id LIKE '%ternary_classifier%'"
    )
    # ### end Alembic commands ###
