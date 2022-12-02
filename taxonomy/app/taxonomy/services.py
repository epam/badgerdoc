from typing import Dict, List, Optional, Tuple, Union

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.models import (
    AssociationTaxonomyCategory,
    AssociationTaxonomyJob,
    Taxonomy,
)
from app.schemas import (
    CategoryLinkSchema,
    TaxonomyBaseSchema,
    TaxonomyInputSchema,
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
    session: Session, primary_key: Union[int, str, Tuple[str, int]]
) -> Optional[Taxonomy]:
    taxonomy = session.query(Taxonomy).get(primary_key)
    return taxonomy


def get_latest_taxonomy(
    session: Session,
    taxonomy_id: str,
) -> Optional[Taxonomy]:
    return (
        session.query(Taxonomy)
        .filter(
            Taxonomy.id == taxonomy_id, Taxonomy.latest == True  # noqa E712
        )
        .first()
    )


def update_taxonomy_instance(
    session: Session,
    taxonomy: Taxonomy,
    new_data: TaxonomyBaseSchema,
) -> Optional[Taxonomy]:
    for key, value in new_data.dict().items():
        if key == "id":
            continue
        setattr(taxonomy, key, value)
    session.commit()
    session.refresh(taxonomy)
    return taxonomy


def delete_taxonomy_instance(session: Session, taxonomy: Taxonomy) -> None:
    session.delete(taxonomy)
    session.commit()


def get_second_latest_taxonomy(
    session: Session, taxonomy_id: str
) -> Optional[Taxonomy]:
    return (
        session.query(Taxonomy)
        .filter(Taxonomy.id == taxonomy_id)
        .order_by(desc(Taxonomy.version))
        .offset(1)
        .first()
    )


def create_new_relation_to_job(
    session: Session, taxonomy: Taxonomy, job_id: str
) -> None:
    new_relation = AssociationTaxonomyJob(
        taxonomy_id=taxonomy.id,
        taxonomy_version=taxonomy.version,
        job_id=job_id,
    )
    session.add(new_relation)
    session.commit()


def get_taxonomies_by_job_id(session: Session, job_id: str) -> List[Taxonomy]:
    taxonomies_ids = tuple(
        session.query(AssociationTaxonomyJob.taxonomy_id)
        .filter(AssociationTaxonomyJob.job_id == job_id)
        .all()
    )
    return (
        session.query(Taxonomy)
        .filter(
            Taxonomy.id.in_(taxonomies_ids),  # type: ignore
            Taxonomy.latest == True,  # noqa E712
        )
        .all()
    )


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
        )
        for link in category_links
    ]
    session.bulk_save_objects(objects)
    session.commit()


def batch_versioned_taxonomies(
    session: Session, schemas: List[CategoryLinkSchema]
) -> Dict[str, int]:
    taxonomies = session.query(Taxonomy.id, Taxonomy.version).filter(
        or_(
            *[
                and_(
                    Taxonomy.id == link.taxonomy_id,
                    Taxonomy.version == link.taxonomy_version,
                )
                for link in schemas
            ]
        )
    )
    return {id_: version for id_, version in taxonomies.all()}


def batch_latest_taxonomies(
    session: Session, schemas: List[CategoryLinkSchema]
) -> Dict[str, int]:
    taxonomies = session.query(Taxonomy.id, Taxonomy.version).filter(
        or_(
            *[
                and_(
                    Taxonomy.id == link.taxonomy_id,
                    Taxonomy.latest == True,  # noqa E712
                )
                for link in schemas
            ]
        )
    )
    return {id_: version for id_, version in taxonomies.all()}


def bulk_delete_category_association(
    session: Session,
    category_id: str,
) -> None:
    session.query(AssociationTaxonomyCategory).filter(
        AssociationTaxonomyCategory.category_id == category_id,
    ).delete(synchronize_session=False)
    session.commit()
