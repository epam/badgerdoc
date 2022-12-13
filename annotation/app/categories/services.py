import uuid
from typing import Dict, List, Optional, Set, Tuple, Union

from cachetools import TTLCache, cached, keys
from filter_lib import Page, form_query, map_request_to_filter, paginate
from sqlalchemy import and_, null, or_
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from sqlalchemy_utils import Ltree
from tenant_dependency import TenantData

from app import logger as app_logger
from app.errors import (
    CheckFieldError,
    ForeignKeyError,
    NoSuchCategoryError,
    SelfParentError,
)
from app.filters import CategoryFilter
from app.microservice_communication.taxonomy import send_category_taxonomy_link
from app.models import Category, Job
from app.schemas import (
    CategoryDataAttributeNames,
    CategoryInputSchema,
    CategoryORMSchema,
    CategoryResponseSchema,
)

cache = TTLCache(maxsize=128, ttl=300)


logger = app_logger.Logger


def is_category_leaf(db: Session, category: Category, tenant: str) -> bool:
    return not (
        db.query(Category.id)
        .filter(
            and_(
                Category.parent == category.id,
                or_(Category.tenant == tenant, Category.tenant == null()),
            )
        )
        .first()
    )


def set_parents_is_leaf(
    category_db: Category,
    parents: Optional[List[CategoryResponseSchema]] = None,
    is_leaf: bool = False,
) -> CategoryResponseSchema:
    if parents is None:
        parents = []
    category_response = response_object_from_db(category_db)
    category_response.is_leaf = is_leaf
    category_response.parents = parents
    return category_response


def insert_category_tree(
    db: Session, category_db: Category, tenant: str
) -> CategoryResponseSchema:
    parents = fetch_category_parents(db, category_db)
    is_leaf = is_category_leaf(db, category_db, tenant)
    category_response = response_object_from_db(category_db)
    if category_response.parent:
        category_response.parents = [
            set_parents_is_leaf(category) for category in parents
        ]
    category_response.is_leaf = is_leaf
    return category_response


def add_category_db(
    db: Session, category_input: CategoryInputSchema, tenant: str
) -> Category:
    name = category_input.name
    id_ = category_input.id
    parent = category_input.parent
    if parent is not None and id_ == parent:
        raise SelfParentError("Category cannot be its own parent.")
    if id_:
        check_unique_category_field(db, id_, "id", tenant)
    check_unique_category_field(db, name, "name", tenant)
    parent = category_input.parent
    parent_db = db.query(Category).get(parent) if parent else None

    if parent_db and parent_db.tenant not in [tenant, None]:
        raise ForeignKeyError("Category with this id doesn't exist.")

    id_ = id_ or uuid.uuid4().hex
    if parent_db and parent_db.tree:
        tree = Ltree(f"{parent_db.tree.path}.{id_}")
    else:
        tree = Ltree(f"{id_}")

    category = Category(
        id=id_,
        name=name,
        tenant=tenant,
        parent=parent if parent != "null" else None,
        metadata_=category_input.metadata,
        editor=category_input.editor,
        data_attributes=category_input.data_attributes,
        type=category_input.type,
        tree=tree,
    )
    db.add(category)
    db.commit()
    return category


def response_object_from_db(category_db: Category) -> CategoryResponseSchema:
    category_orm = CategoryORMSchema.from_orm(category_db).dict()
    return CategoryResponseSchema.parse_obj(category_orm)


def fetch_category_parents(
    db: Session, category_input: Category
) -> List[Category]:
    return (
        db.query(Category)
        .filter(Category.tree.ancestor_of(category_input.tree))
        .order_by(Category.tree.asc())
        .all()[:-1]
    )  # remove self item from result


def fetch_category_children(
    db: Session, category_input: Category
) -> List[Category]:
    return (
        db.query(Category)
        .filter(Category.tree.descendant_of(category_input.tree))
        .offset(1)
        .all()
    )


def check_unique_category_field(
    db: Session, value: str, field: str, tenant: str
) -> None:
    check_unique = db.query(
        db.query(Category)
        .filter(or_(Category.tenant == tenant, Category.tenant == null()))
        .filter_by(**{field: value})
        .exists()
    ).scalar()
    if check_unique:
        raise CheckFieldError(f"Category {field} must be unique.")


def fetch_category_db(db: Session, category_id: str, tenant: str) -> Category:
    category = db.query(Category).get(category_id)
    if not category or category.tenant and category.tenant != tenant:
        raise NoSuchCategoryError(
            f"Category with id: {category_id} doesn't exist"
        )
    return category


@listens_for(Category, "after_insert")
@listens_for(Category, "after_update")
@listens_for(Category, "after_delete")
def clear_child_categories_cache(*_):
    """Clears cache for recursive_subcategory_search everytime
    when categories table modified"""
    cache.clear()


def key_without_db_session(*args):
    """Returns cache key for each set of params given to
    recursive_subcategory_search. Session param should
    be excluded because it is unique for every call"""
    args_without_session = [arg for arg in args if isinstance(arg, str)]
    key = keys.hashkey(*args_without_session)
    return key


@cached(cache=cache, key=key_without_db_session)
def recursive_subcategory_search(
    db: Session, category: str, root_id: str, child_categories: Set[str]
):
    """Recursively searches through the parent-child hierarchy tree of
    categories and adds all subcategories for category into 'child_categories'
    set. Note that due to 'not-self-parent' constraint category cannot be
    self-parent directly, but in possible cyclic parent-child relationships
    category may occur as child of some self subcategories. In that case code
    logic prevents infinite recursion but root category should be explicitly
    discarded from returning 'child_categories' set.
    """
    skipped_categories = {*child_categories, category, root_id}
    child_ids = [
        child.id
        for child in db.query(Category).filter_by(parent=category).all()
        if child.id not in skipped_categories
    ]
    if child_ids:
        child_categories.update(child_ids)
        for child_id in child_ids:
            recursive_subcategory_search(
                db, child_id, root_id, child_categories
            )
    return child_categories


def fetch_bunch_categories_db(
    db: Session,
    category_ids: Set[str],
    tenant: str,
    job_id: Optional[int] = None,
    root_parents: bool = False,  # If true, add categories parents up to root
) -> List[Category]:
    categories_query = db.query(Category)
    if job_id is not None:
        categories_query = categories_query.join(Category.jobs).filter(
            Job.job_id == job_id
        )
    categories = categories_query.filter(
        and_(
            Category.id.in_(category_ids),
            or_(Category.tenant == tenant, Category.tenant == null()),
        )
    ).all()
    if root_parents:
        categories_parents = _get_parents(db, categories, tenant, job_id)
        categories = list(
            set(categories).union(
                cat for cats in categories_parents.values() for cat in cats
            )
        )
    wrong_categories = {
        category.id for category in categories
    }.symmetric_difference(category_ids)

    if wrong_categories:
        error_message = ", ".join(sorted(wrong_categories))
        raise NoSuchCategoryError(f"No such categories: {error_message}")
    return categories


CategoryIdT = str
CategoryPathT = str
IsLeafT = bool
Leaves = Dict[CategoryIdT, IsLeafT]
Parents = Dict[CategoryPathT, List[Category]]


def _get_leaves(
    db: Session,
    categories: List[Category],
    tenant: str,
    job_id: Optional[int] = None,
) -> Leaves:
    leaves: Leaves = {c.id: True for c in categories}
    categories_query = db.query(Category)
    if job_id is not None:
        categories_query = categories_query.join(Category.jobs).filter(
            Job.job_id == job_id
        )
    categories_query = categories_query.filter(
        and_(
            Category.parent.in_(leaves.keys()),
            or_(Category.tenant == tenant, Category.tenant == null()),
        )
    )
    for child in categories_query.all():
        leaves[child.parent] = False
    return leaves


def _extract_category(
    path: str, categories: Dict[str, Category]
) -> List[Category]:
    return [
        CategoryResponseSchema.parse_obj(
            {
                **CategoryORMSchema.from_orm(categories[node]).dict(),
                "is_leaf": False,
            }
        )
        for node in path.split(".")[0:-1]
    ]


def _get_parents(
    db: Session,
    categories: List[Category],
    tenant: str,
    job_id: Optional[int] = None,
) -> Parents:
    path_to_category: Parents = {}
    uniq_cats = set()
    uniq_pathes = set()

    for cat in categories:
        # if we pass root categories it causes exception.
        if cat.tree is not None:
            uniq_pathes.add(cat.tree.path)
            uniq_cats = uniq_cats.union({tree.path for tree in cat.tree})

    category_to_object = {
        cat.id: cat
        for cat in fetch_bunch_categories_db(db, uniq_cats, tenant, job_id)
    }

    for path in uniq_pathes:
        path_to_category[path] = _extract_category(path, category_to_object)

    return path_to_category


def _compose_response(
    categories: List[Category], leaves: Leaves, parents: Parents
) -> List[CategoryResponseSchema]:
    return [
        CategoryResponseSchema.parse_obj(
            {
                **CategoryORMSchema.from_orm(cat).dict(),
                "is_leaf": leaves.get(cat.id, False),
                "parents": parents.get(cat.tree.path, []),
            }
        )
        for cat in categories
    ]


def _get_child_categories(
    db: Session,
    request: CategoryFilter,
    tenant: str,
    job_id: Optional[int] = None,
) -> Tuple:
    categories_query = db.query(Category)
    if job_id is not None:
        categories_query = categories_query.join(Category.jobs).filter(
            and_(Job.job_id == job_id, Job.tenant == tenant)
        )
    else:
        categories_query = categories_query.filter(
            or_(Category.tenant == tenant, Category.tenant == null())
        )

    filter_args = map_request_to_filter(request.dict(), Category.__name__)
    category_query, pagination = form_query(filter_args, categories_query)
    return category_query.all(), pagination


def filter_category_db(
    db: Session,
    request: CategoryFilter,
    tenant: str,
    job_id: Optional[int] = None,
) -> Page[Union[CategoryResponseSchema, str, dict]]:
    child_categories, pagination = _get_child_categories(
        db, request, tenant, job_id
    )

    if request.filters and "distinct" in [
        item.operator.value for item in request.filters
    ]:
        return paginate(child_categories, pagination)

    return paginate(
        _compose_response(
            child_categories,
            _get_leaves(db, child_categories, tenant, job_id),
            _get_parents(db, child_categories, tenant, job_id),
        ),
        pagination,
    )


def update_category_tree(
    db: Session,
    category_db: Category,
    new_parent: Category = None,
) -> None:
    tree = category_db.tree
    nlevel = len(tree) - 1
    query = db.query(Category).filter(Category.tree.op("<@")(tree))

    new_path = func.subpath(Category.tree, nlevel)
    if new_parent:
        new_path = new_parent.tree.path + new_path

    query.update(values={"tree": new_path}, synchronize_session=False)


def update_category_db(
    db: Session, category_id: str, update_query: dict, tenant: str
) -> Category:
    category = db.query(Category).get(category_id)
    if not category or category.tenant not in [tenant, None]:
        raise NoSuchCategoryError("Cannot update category that doesn't exist")
    elif category.tenant is None:
        raise CheckFieldError("Cannot update default category.")
    if category_id == update_query["parent"]:
        raise SelfParentError("Category cannot be its own parent.")
    update_query["parent"] = (
        update_query["parent"] if update_query["parent"] != "null" else None
    )
    ex_parent_id = category.parent
    new_parent_id = update_query["parent"]
    parent_db = (
        db.query(Category).get(new_parent_id) if new_parent_id else None
    )

    if parent_db and parent_db.tenant not in [tenant, None]:
        raise ForeignKeyError("Category with this id doesn't exist.")

    name = (update_query["name"],)
    check_unique = (
        db.query(Category)
        .filter(or_(Category.tenant == tenant, Category.tenant == null()))
        .filter_by(name=name)
        .first()
    )
    if update_query["name"] != category.name and check_unique:
        raise CheckFieldError("Category name must be unique.")

    update_query["metadata_"] = update_query.get("metadata")
    update_query["id"] = category_id
    for field, value in update_query.items():
        setattr(category, field, value)

    if ex_parent_id != new_parent_id and category.tree:
        update_category_tree(db, category, parent_db)

    db.add(category)
    db.commit()
    return category


def delete_category_db(db: Session, category_id: str, tenant: str) -> None:
    category = db.query(Category).get(category_id)
    if not category or category.tenant not in [tenant, None]:
        raise NoSuchCategoryError("Cannot delete category that doesn't exist")
    elif category.tenant is None:
        raise CheckFieldError("Cannot delete default category.")
    db.delete(category)
    db.commit()


def link_category_with_taxonomy(
    category_db: Category,
    x_current_tenant: str,
    token: TenantData,
):
    if category_db.data_attributes:
        taxonomy_link_params = []
        for data_attribute in category_db.data_attributes:
            if CategoryDataAttributeNames.validate_schema(data_attribute):
                taxonomy_link_params.append(data_attribute)

        if taxonomy_link_params:
            send_category_taxonomy_link(
                category_id=category_db.id,
                tenant=x_current_tenant,
                token=token.token,
                taxonomy_link_params=taxonomy_link_params,
            )
