from typing import List

from sqlalchemy import and_, func, null, or_
from sqlalchemy.orm import Session
from sqlalchemy_utils import Ltree

from app.errors import (
    CheckFieldError,
    ForeignKeyError,
    SelfParentError,
    NoTaxonError,
)
from app.models import Taxon, Taxonomy
from app.schemas import (
    TaxonInputSchema,
    TaxonResponseSchema,
)


def response_object_from_db():
    # TODO
    pass


def add_taxon_db(
    db: Session, taxon_input: TaxonInputSchema, tenant: str
) -> Taxon:
    name = taxon_input.name
    id_ = taxon_input.id
    parent_id = taxon_input.parent_id
    taxonomy_id = taxon_input.taxonomy_id

    if parent_id is not None and id_ == parent_id:
        raise SelfParentError("Taxon cannot be its own parent.")
    if id_:
        check_unique_taxon_field(db, id_, "id", tenant)
    check_unique_taxon_field(db, name, "name", tenant)

    parent_db = db.query(Taxon).get(parent_id) if parent_id else None
    if parent_db and parent_db.tenant not in [tenant, None]:
        raise ForeignKeyError("Taxon with this id doesn't exist.")

    taxonomy_db = db.query(Taxonomy).get(taxonomy_id)
    if taxonomy_db and taxonomy_db.tenant not in [tenant, None]:
        raise ForeignKeyError("Taxonomy with this id doesn't exist.")

    if parent_db and parent_db.tree:
        tree = Ltree(f'{parent_db.tree.path}.{taxon_input.id}')
    else:
        tree = Ltree(f'{taxon_input.id}')

    taxon = Taxon(
        id=id_,
        name=name,
        tenant=tenant,
        taxonomy_id=taxonomy_id,
        parent_id=parent_id if parent_id != "null" else None,
        tree=tree,
    )
    db.add(taxon)
    db.commit()
    return taxon


def fetch_taxon_db(db: Session, taxon_id: str, tenant: str) -> Taxon:
    taxon = db.query(Taxon).get(taxon_id)
    if not taxon or taxon.tenant and taxon.tenant != tenant:
        raise NoTaxonError(
            f"Taxon with id: {taxon_id} doesn't exist"
        )
    return taxon


def fetch_taxon_parents(db: Session, taxon_input: Taxon) -> List[Taxon]:
    return db.query(Taxon).filter(
        Taxon.tree.ancestor_of(taxon_input.tree)
    ).order_by(Taxon.tree.desc()).offset(1).all()


def has_children(db: Session, taxon_input: Taxon) -> bool:
    # TODO
    return False


def insert_taxon_tree(
    db: Session, taxon_db: Taxon
) -> TaxonResponseSchema:
    parents = fetch_taxon_parents(db, taxon_db)
    is_leaf = has_children(db, taxon_db)

    taxon_response = response_object_from_db(taxon_db)

    if taxon_response.parent_id:
        taxon_response.parents = [
            response_object_from_db(taxon) for taxon in parents
        ]
    taxon_response.is_leaf = is_leaf
    return taxon_response


def update_taxon_tree(
    db: Session, taxon_db: Taxon, new_parent: Taxon = None,
) -> None:
    tree = taxon_db.tree
    nlevel = len(tree) - 1
    query = db.query(Taxon).filter(Taxon.tree.op('<@')(tree))

    new_path = func.subpath(Taxon.tree, nlevel)
    if new_parent:
        new_path = new_parent.tree.path + new_path

    query.update(values={'tree': new_path}, synchronize_session=False)


def update_taxon_db(
    db: Session, taxon_id: str, update_query: dict, tenant: str
) -> Taxon:
    taxon = db.query(Taxon).get(taxon_id)

    if not taxon or taxon.tenant not in [tenant, None]:
        raise NoTaxonError("Cannot update taxon that doesn't exist")
    elif taxon.tenant is None:
        raise CheckFieldError("Cannot update default taxon.")
    if taxon_id == update_query["parent_id"]:
        raise SelfParentError("Taxon cannot be its own parent.")

    update_query["parent_id"] = (
        update_query["parent_id"] if update_query["parent_id"] != "null" else None
    )
    ex_parent_id = taxon.parent_id
    new_parent_id = update_query["parent_id"]
    parent_db = db.query(Taxon).get(new_parent_id) if new_parent_id else None

    if parent_db and parent_db.tenant not in [tenant, None]:
        raise ForeignKeyError("Taxon with this parent_id doesn't exist.")

    name = (update_query["name"],)
    check_unique = (
        db.query(Taxon)
        .filter(or_(Taxon.tenant == tenant, Taxon.tenant == null()))
        .filter_by(name=name)
        .first()
    )
    if update_query["name"] != taxon.name and check_unique:
        raise CheckFieldError("Taxon name must be unique.")

    update_query["id"] = taxon_id
    for field, value in update_query.items():
        setattr(taxon, field, value)

    if ex_parent_id != new_parent_id and taxon.tree:
        update_taxon_tree(db, taxon, parent_db)

    db.add(taxon)
    db.commit()
    return taxon


def delete_taxon_db(db: Session, taxon_id: str, tenant: str) -> None:
    taxon = db.query(Taxon).get(taxon_id)
    if not taxon or taxon.tenant not in [tenant, None]:
        raise NoTaxonError("Cannot delete taxon that doesn't exist")
    elif taxon.tenant is None:
        raise CheckFieldError("Cannot delete default taxon.")
    db.delete(taxon)
    db.commit()


def check_unique_taxon_field(
    db: Session, value: str, field: str, tenant: str
) -> None:
    check_unique = db.query(
        db.query(Taxon)
        .filter(or_(Taxon.tenant == tenant, Taxon.tenant == null()))
        .filter_by(**{field: value})
        .exists()
    ).scalar()
    if check_unique:
        raise CheckFieldError(f"Taxon {field} must be unique.")