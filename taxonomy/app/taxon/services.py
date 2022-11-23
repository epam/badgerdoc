from typing import List, Union, Dict, Tuple, Set

from filter_lib import Page, paginate, map_request_to_filter, form_query
from sqlalchemy import and_, func, null, or_
from sqlalchemy.orm import Session, query
from sqlalchemy_utils import Ltree

from app.filters import TaxonFilter
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

TaxonIdT = str
TaxonPathT = str
IsLeafT = bool
Leafs = Dict[TaxonIdT, IsLeafT]
Parents = Dict[TaxonPathT, Taxon]


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
    ).order_by(Taxon.tree.asc()).all()[:-1]


def is_taxon_leaf(db: Session, taxon_input: Taxon, tenant: str) -> bool:
    return not (
        db.query(Taxon.id)
        .filter(
            and_(
                Taxon.parent_id == taxon_input.id,
                or_(Taxon.tenant == tenant, Taxon.tenant == null())
            )).first()
    )


def set_parents_is_leaf(taxon_db: List[Taxon]) -> TaxonResponseSchema:
    taxon_response = TaxonResponseSchema.from_orm(taxon_db)
    taxon_response.is_leaf = False
    return taxon_response


def insert_taxon_tree(
    db: Session, taxon_db: Taxon, tenant: str,
) -> TaxonResponseSchema:
    parents = fetch_taxon_parents(db, taxon_db)
    is_leaf = is_taxon_leaf(db, taxon_db, tenant)

    taxon_response = TaxonResponseSchema.from_orm(taxon_db)

    if taxon_response.parent_id:
        taxon_response.parents = [
            set_parents_is_leaf(taxon) for taxon in parents
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
        update_query["parent_id"]
        if update_query["parent_id"] != "null" else None
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


def _get_leafs(db: Session, taxons: List[Taxon], tenant: str) -> Leafs:
    leafs: Leafs = {t.id: True for t in taxons}
    for child in (
        # TODO doublecheck select only ids
        db.query(Taxon.id)
        .filter(
            and_(
                Taxon.parent_id.in_(leafs.keys()),
                or_(Taxon.tenant == tenant, Taxon.tenant == null()),
            )
        )
        .all()
    ):
        leafs[child.parent_id] = False
    return leafs


def _get_child_taxons(
    db: Session, request: TaxonFilter, tenant: filter, filter_query=None
) -> Tuple:

    if filter_query is None:
        filter_query = db.query(Taxon).filter(
            or_(Taxon.tenant == tenant, Taxon.tenant == null())
        )

    filter_args = map_request_to_filter(request.dict(), Taxon.__name__)
    taxon_query, pagination = form_query(filter_args, filter_query)
    return taxon_query.all(), pagination


def _extract_taxon(
    path: str, taxons: Dict[str, Taxon]
) -> List[Taxon]:
    return [
        {
            **TaxonResponseSchema.from_orm(taxons[node]).dict(),
            "is_leaf": False,
        } for node in path.split(".")[0:-1]
    ]


def _get_parents(
    db: Session, taxons: List[Taxon], tenant: str
) -> Parents:
    path_to_taxon: Parents = {}
    unique_taxons = set()
    unique_pathes = set()

    for tax in taxons:
        unique_pathes.add(tax.tree.path)
        unique_taxons = unique_taxons.union({tree.path for tree in tax.tree})

    taxon_to_object = {
        tax.id: tax for tax in fetch_bunch_taxons_db(db, unique_taxons, tenant)
    }

    for path in unique_pathes:
        path_to_taxon[path] = _extract_taxon(path, taxon_to_object)

    return path_to_taxon


def fetch_bunch_taxons_db(
    db: Session, taxon_ids: Set[str], tenant: str
) -> List[Taxon]:
    taxons = (
        db.query(Taxon)
        .filter(
            and_(
                Taxon.id.in_(taxon_ids),
                or_(Taxon.tenant == tenant, Taxon.tenant == null()),
            )
        )
        .all()
    )
    taxons_not_exist = {
        taxon.id for taxon in taxons
    }.symmetric_difference(taxon_ids)
    error_message = ", ".join(sorted(taxons_not_exist))
    if taxons_not_exist:
        raise NoTaxonError(f"No such taxons: {error_message}")
    return taxons


def _compose_response(
    taxons: List[Taxon], leafs: Leafs, parents: Parents
) -> List[TaxonResponseSchema]:
    return [
        {
            **TaxonResponseSchema.from_orm(tax).dict(),
            "is_leaf": leafs.get(tax.id, False),
            "parents": parents.get(tax.tree.path, []),
        } for tax in taxons
    ]


def filter_taxons(
    db: Session,
    request: TaxonFilter,
    tenant: str,
    query: query = None,
) -> Page[Union[TaxonResponseSchema, str, dict]]:
    child_taxons, pagination = _get_child_taxons(
        db, request, tenant, query
    )

    if request.filters and "distinct" in [
        item.operator.value for item in request.filters
    ]:
        return paginate(child_taxons, pagination)

    return paginate(
        _compose_response(
            child_taxons,
            _get_leafs(db, child_taxons, tenant),
            _get_parents(db, child_taxons, tenant),
        ),
        pagination,
    )
