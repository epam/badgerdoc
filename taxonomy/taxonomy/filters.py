from filter_lib import create_filter_model

from taxonomy.models import Taxon

TaxonFilter = create_filter_model(Taxon, exclude=["tenant"])
