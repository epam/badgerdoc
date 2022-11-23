from typing import Dict, Union, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from models import Taxonomy
from schemas import TaxonomyInputSchema, TaxonomyBaseSchema


def response_object_from_db(taxonomy: Taxonomy):
    # todo get taxon ltree object here
    pass


def create_taxonomy_instance(
    session: Session,
    tenant: str,
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


def get_latest_taxonomy(session: Session, taxonomy_id: str) -> Optional[Taxonomy]:
    return (
        session.query(Taxonomy)
        .filter(Taxonomy.id == taxonomy_id, Taxonomy.latest == True)  # noqa E712
        .first()
    )


def update_taxonomy_instance(
    session: Session,
    taxonomy: Taxonomy,
    new_data: TaxonomyBaseSchema,
) -> Optional[Taxonomy]:
    for key, value in new_data.dict():
        if key == 'id':
            continue
        setattr(taxonomy, key, value)
    session.commit()
    session.refresh(taxonomy)
    return taxonomy


def delete_taxonomy_instance(
    session: Session, taxonomy: Taxonomy
) -> None:
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