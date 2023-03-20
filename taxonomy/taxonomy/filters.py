from filter_lib import create_filter_model

from taxonomy.models import Taxon, Taxonomy

TaxonFilter = create_filter_model(Taxon, exclude=["tenant"])
TaxonomyFilter = create_filter_model(Taxonomy, exclude=["tenant"])
