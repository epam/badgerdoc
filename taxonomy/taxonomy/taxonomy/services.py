from typing import Dict, List, Optional, Tuple, Union

from filter_lib import Page, form_query, map_request_to_filter, paginate
from sqlalchemy import and_, desc, null, or_
from sqlalchemy.orm import Query, Session

from taxonomy.errors import CheckFieldError
from taxonomy.filters import TaxonomyFilter
from taxonomy.models import AssociationTaxonomyCategory, Taxonomy
from taxonomy.schemas import (
    CategoryLinkSchema,
    JobTaxonomySchema,
    TaxonomyBaseSchema,
    TaxonomyInputSchema,
    TaxonomyResponseSchema,
)


def create_taxonomy_instance(
    session: Session,
    tenant: Optional[str],
    args: TaxonomyInputSchema,
    taxonomy_args: Dict[str, Union[int, bool]] = None,
) -> Taxonomy:
    instance_args = args.dict()
    instance_args.update(taxonomy_args)
    instance = Taxonomy(**instance_args, tenant=tenant)
    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance


def get_taxonomy(
    session: Session,
    primary_key: Union[int, str, Tuple[str, int]],
    tenant: str,
) -> Optional[Taxonomy]:
    taxonomy = session.query(Taxonomy).get(primary_key)
    if taxonomy and taxonomy.tenant in (tenant, None):
        return taxonomy
    else:
        raise CheckFieldError("Taxonomy is not associated with current tenant")


def get_latest_taxonomy(
    session: Session,
    taxonomy_id: str,
    tenant: str,
) -> Optional[Taxonomy]:
    return (
        session.query(Taxonomy)
        .filter(
            and_(
                Taxonomy.id == taxonomy_id,
                Taxonomy.latest == True,  # noqa E712
                or_(Taxonomy.tenant.in_((tenant, None))),
            )
        )
        .first()
    )


def update_taxonomy_instance(
    session: Session,
    taxonomy: Taxonomy,
    new_data: TaxonomyBaseSchema,
    tenant: str,
) -> Optional[Taxonomy]:
    for key, value in new_data.dict().items():
        if key == "id" or taxonomy.tenant not in (tenant, None):
            continue
        setattr(taxonomy, key, value)
    session.commit()
    session.refresh(taxonomy)
    return taxonomy


def delete_taxonomy_instance(
    session: Session,
    taxonomy: Taxonomy,
    tenant: str,
) -> None:
    if taxonomy and taxonomy.tenant in (tenant, None):
        session.delete(taxonomy)
        session.commit()
    else:
        raise CheckFieldError("Taxonomy is not associated with current tenant")


def get_second_latest_taxonomy(
    session: Session,
    taxonomy_id: str,
    tenant: str,
) -> Optional[Taxonomy]:
    return (
        session.query(Taxonomy)
        .filter(Taxonomy.id == taxonomy_id)
        .filter(Taxonomy.tenant.in_((tenant, None)))
        .order_by(desc(Taxonomy.version))
        .offset(1)
        .first()
    )


def get_taxonomies_by_job_id(
    session: Session, job_id: str, x_current_tenant: str
) -> List[JobTaxonomySchema]:
    job_taxonomies = (
        session.query(
            Taxonomy.name,
            Taxonomy.id,
            Taxonomy.version,
            AssociationTaxonomyCategory.category_id,
        )
        .join(Taxonomy.categories)
        .filter(
            AssociationTaxonomyCategory.job_id == job_id,
            Taxonomy.tenant == x_current_tenant,
            Taxonomy.latest == True,  # noqa E712
        )
    )
    return [
        JobTaxonomySchema(
            name=name,
            id=id,
            version=version,
            category_id=category_id,
        )
        for name, id, version, category_id in job_taxonomies.all()
    ]


def get_linked_taxonomies(
    session: Session, job_id: str, category_id: str, x_current_tenant: str
) -> List[TaxonomyResponseSchema]:
    linked_taxonomies = (
        session.query(
            Taxonomy.name,
            Taxonomy.id,
            Taxonomy.version,
        )
        .join(Taxonomy.categories)
        .filter(
            AssociationTaxonomyCategory.job_id == job_id,
            AssociationTaxonomyCategory.category_id == category_id,
            Taxonomy.tenant == x_current_tenant,
            Taxonomy.latest == True,  # noqa E712
        )
    )
    return [
        TaxonomyResponseSchema(
            name=name,
            id=id,
            version=version,
        )
        for name, id, version in linked_taxonomies.all()
    ]


def bulk_create_relations_with_categories(
    session: Session,
    taxonomies: Dict[str, int],
    category_links: List[CategoryLinkSchema],
) -> None:
    objects = [
        AssociationTaxonomyCategory(
            taxonomy_id=link.taxonomy_id,
            taxonomy_version=taxonomies[link.taxonomy_id],
            category_id=link.category_id,
            job_id=link.job_id,
        )
        for link in category_links
    ]
    session.bulk_save_objects(objects)
    session.commit()


def batch_versioned_taxonomies(
    session: Session, schemas: List[CategoryLinkSchema], tenant: str
) -> Dict[str, int]:
    taxonomies = session.query(Taxonomy.id, Taxonomy.version).filter(
        or_(
            *[
                and_(
                    Taxonomy.id == link.taxonomy_id,
                    Taxonomy.version == link.taxonomy_version,
                    or_(Taxonomy.tenant.in_((tenant, None))),
                )
                for link in schemas
            ]
        )
    )
    return {id_: version for id_, version in taxonomies.all()}


def batch_latest_taxonomies(
    session: Session, schemas: List[CategoryLinkSchema], tenant: str
) -> Dict[str, int]:
    taxonomies = session.query(Taxonomy.id, Taxonomy.version).filter(
        or_(
            *[
                and_(
                    Taxonomy.id == link.taxonomy_id,
                    Taxonomy.latest == True,  # noqa E712
                    Taxonomy.tenant.in_((tenant, None)),
                )
                for link in schemas
            ]
        )
    )
    return {id_: version for id_, version in taxonomies.all()}


def bulk_delete_category_association(
    session: Session,
    tenant: str,
    job_id: str,
    category_id: Optional[str] = None,
) -> None:
    tenant_taxonomy = session.query(Taxonomy.id, Taxonomy.version).filter(
        Taxonomy.tenant == tenant,
    )
    taxonomy_links = session.query(AssociationTaxonomyCategory).filter(
        AssociationTaxonomyCategory.job_id == job_id,
    )
    if category_id:
        taxonomy_links.filter(
            AssociationTaxonomyCategory.category_id == category_id,
        )
    taxonomy_links.filter(
        AssociationTaxonomyCategory.taxonomy_id.in_(
            tenant_taxonomy.subquery()
        ),
        AssociationTaxonomyCategory.taxonomy_version.in_(
            tenant_taxonomy.subquery()
        ),
    )
    taxonomy_links.delete(synchronize_session=False)
    session.commit()


def _get_obj_from_request(
    db: Session, request: TaxonomyFilter, tenant: str, filter_query=None
) -> Tuple:

    if filter_query is None:
        filter_query = db.query(Taxonomy).filter(
            or_(Taxonomy.tenant == tenant, Taxonomy.tenant == null())
        )

    filter_args = map_request_to_filter(request.dict(), Taxonomy.__name__)
    taxonomy_query, pagination = form_query(filter_args, filter_query)
    return taxonomy_query.all(), pagination


def filter_taxonomies(
    db: Session,
    request: TaxonomyFilter,
    tenant: str,
    query: Optional[Query] = None,
) -> Page[Union[TaxonomyResponseSchema, str, dict]]:
    taxonomies_request, pagination = _get_obj_from_request(
        db, request, tenant, query
    )

    return paginate(taxonomies_request, pagination)
