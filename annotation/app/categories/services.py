import uuid
from typing import List, Set

from cachetools import TTLCache, cached, keys
from filter_lib import Page, form_query, map_request_to_filter, paginate
from sqlalchemy import and_, null, or_
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

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
    category = Category(
        id=(id_ or str(uuid.uuid4())),
        name=name,
        tenant=tenant,
        parent=parent if parent != "null" else None,
        metadata_=category_input.metadata,
        editor=category_input.editor,
        data_attributes=category_input.data_attributes,
        type=category_input.type,
    )
    db.add(category)
    db.commit()
    return category


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
    if request.filters and "distinct" in [
        item.operator.value for item in request.filters
    ]:
        return paginate(category_query.all(), pagination)
    categories_db = (
        CategoryORMSchema.from_orm(category) for category in category_query
    )
    return paginate(
        [
            CategoryResponseSchema.parse_obj(category_db.dict())
            for category_db in categories_db
        ],
        pagination,
    )


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
    parent = update_query["parent"]
    parent_db = db.query(Category).get(parent) if parent else None
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


def get_random_category_ids(db: Session, count: int) -> List[str]:
    random_ids = [
        item.id
        for item in db.query(Category.id).order_by(func.random()).limit(count)
    ]
    return random_ids


def insert_mock_categories(
    db: Session, task_response: paginate, random_ids: List[str]
) -> paginate:

    random_categories = db.query(Category).filter(Category.id.in_(random_ids))

    categories_db = (
        CategoryORMSchema.from_orm(category) for category in random_categories
    )
    mock_items = [
        CategoryResponseSchema.parse_obj(category_db.dict())
        for category_db in categories_db
    ]
    for entity in task_response.data:
        if not entity.parent:
            entity.children = mock_items
        else:
            entity.parents = mock_items

    return task_response


def modify_single_category(
    db: Session, category_response: CategoryResponseSchema, random_ids: List[str]
) -> CategoryResponseSchema:

    random_categories = db.query(Category).filter(Category.id.in_(random_ids))

    categories_db = (
        CategoryORMSchema.from_orm(category) for category in random_categories
    )
    mock_items = [
        CategoryResponseSchema.parse_obj(category_db.dict())
        for category_db in categories_db
    ]
    if not category_response.parent:
            category_response.children = mock_items
    else:
        category_response.parents = mock_items

    return category_response