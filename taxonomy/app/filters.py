from filter_lib import create_filter_model

from app.models import Taxon

TaxonFilter = create_filter_model(Taxon, exclude=["tenant"])
