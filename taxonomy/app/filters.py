
from filter_lib import create_filter_model

from app.models import Taxon

TaxonFilter = create_filter_model(
    Taxon,
    exclude=[
        "tenant",
        "data_attributes",
        # *[f"parent_id.{col}" for col in Category.__table__.columns.keys()],
        # *[f"jobs.{col}" for col in Job.__table__.columns.keys()],
    ],
)
