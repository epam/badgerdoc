"""pod limits column

Revision ID: 826680104247
Revises: abeff4c79fd3
Create Date: 2022-04-07 15:03:51.910752

"""
from json import dumps

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "826680104247"
down_revision = "abeff4c79fd3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "basement",
        sa.Column("limits", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )

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
        f"UPDATE basement SET limits = '{dumps(dod_limits)}' " f"WHERE id LIKE '%dod%'"
    )
    op.execute(
        f"UPDATE basement SET limits = '{dumps(table_extractor_limits)}' "
        f"WHERE id LIKE '%table_extractor%'"
    )
    op.execute(
        f"UPDATE basement SET limits = "
        f"'{dumps(ternary_classifier_limits)}' "
        f"WHERE id LIKE '%ternary_classifier%'"
    )
    op.alter_column("basement", "limits", nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("basement", "limits")
    # ### end Alembic commands ###
