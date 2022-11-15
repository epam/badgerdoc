import uuid
from typing import List, Set

from cachetools import TTLCache, cached, keys
from filter_lib import Page, form_query, map_request_to_filter, paginate
from sqlalchemy import and_, func, null, or_
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from sqlalchemy_utils import Ltree

from app.errors import (
    CheckFieldError,
    ForeignKeyError,
    NoSuchCategoryError,
    SelfParentError,
)
from app.filters import CategoryFilter
from app.models import Category
from app.schemas import (
    CategoryInputSchema,
    CategoryORMSchema,
    CategoryResponseSchema,
)

cache = TTLCache(maxsize=128, ttl=300)


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

    if parent_db and parent_db.tree:
        tree = Ltree(f'{parent_db.tree.path}.{category_input.id}')
    else:
        tree = Ltree(f'{category_input.id}')

    category = Category(
        id=(id_ or str(uuid.uuid4())),
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


def fetch_category_parents(db: Session, category_input: Category) -> List[Category]:
    return db.query(Category).filter(
        Category.tree.ancestor_of(category_input.tree)
    ).order_by(Category.tree.desc()).offset(1).all()


def fetch_category_children(db: Session, category_input: Category) -> List[Category]:
    return db.query(Category).filter(
        Category.tree.descendant_of(category_input.tree)
    ).offset(1).all()


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
    db: Session, category_ids: Set[str], tenant: str
) -> List[Category]:
    categories = (
        db.query(Category)
        .filter(
            and_(
                Category.id.in_(category_ids),
                or_(Category.tenant == tenant, Category.tenant == null()),
            )
        )
        .all()
    )
    wrong_categories = {
        category.id for category in categories
    }.symmetric_difference(category_ids)
    error_message = ", ".join(sorted(wrong_categories))
    if wrong_categories:
        raise NoSuchCategoryError(f"No such categories: {error_message}")
    return categories


def filter_category_db(
    db: Session, request: CategoryFilter, tenant: str
) -> Page[CategoryResponseSchema]:
    filter_query = db.query(Category).filter(
        or_(Category.tenant == tenant, Category.tenant == null())
    )
    filter_args = map_request_to_filter(request.dict(), Category.__name__)
    category_query, pagination = form_query(filter_args, filter_query)

    # Check if filter is valid
    if request.filters and "distinct" in [
        item.operator.value for item in request.filters
    ]:
        return paginate(category_query.all(), pagination)
    return paginate(
        [insert_category_tree(db, category) for category in category_query],
        pagination,
    )


def update_category_tree(
    db: Session, category_db: Category, new_parent: Category = None,
) -> None:
    tree = category_db.tree
    nlevel = len(tree) - 1
    query = db.query(Category).filter(Category.tree.op('<@')(tree))

    new_path = func.subpath(Category.tree, nlevel)
    if new_parent:
        new_path = new_parent.tree.path + new_path

    query.update(values={'tree': new_path}, synchronize_session=False)


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
    parent_db = db.query(Category).get(new_parent_id) if new_parent_id else None

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


def insert_category_tree(
    db: Session, category_db: Category
) -> CategoryResponseSchema:
    parents = fetch_category_parents(db, category_db)
    children = fetch_category_children(db, category_db)

    category_response = response_object_from_db(category_db)

    if category_response.parent:
        category_response.parents = [
            response_object_from_db(category) for category in parents
        ]
    category_response.children = [
        response_object_from_db(category) for category in children
    ]
    return category_response