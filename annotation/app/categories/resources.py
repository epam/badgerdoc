from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from filter_lib import Page
from sqlalchemy.orm import Session
from sqlalchemy_filters.exceptions import BadFilterFormat
from tenant_dependency import TenantData

from app.database import get_db
from app.errors import NoSuchCategoryError
from app.filters import CategoryFilter
from app.microservice_communication.search import X_CURRENT_TENANT_HEADER
from app.microservice_communication.taxonomy import delete_taxonomy_link
from app.schemas import (
    BadRequestErrorSchema,
    CategoryBaseSchema,
    CategoryInputSchema,
    CategoryResponseSchema,
    ConnectionErrorSchema,
    NotFoundErrorSchema,
    SubCategoriesOutSchema,
)
from app.tags import CATEGORIES_TAG
from app.token_dependency import TOKEN

from .services import (
    add_category_db,
    delete_category_db,
    fetch_category_db,
    filter_category_db,
    insert_category_tree,
    link_category_with_taxonomy,
    recursive_subcategory_search,
    response_object_from_db,
    update_category_db,
)

router = APIRouter(
    prefix="/categories",
    tags=[CATEGORIES_TAG],
    responses={500: {"model": ConnectionErrorSchema}},
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryResponseSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Save new category and return saved one.",
)
def save_category(
    category: CategoryInputSchema,
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
) -> CategoryResponseSchema:
    category_db = add_category_db(db, category, x_current_tenant)
    link_category_with_taxonomy(
        category_db=category_db,
        x_current_tenant=x_current_tenant,
        token=token,
    )
    return response_object_from_db(category_db)


# Get by category id, requires children/parents
@router.get(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=CategoryResponseSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get category by id.",
)
def fetch_category(
    category_id: str = Path(..., example="1"),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> CategoryResponseSchema:
    category_db = fetch_category_db(db, category_id, x_current_tenant)
    category_response = insert_category_tree(
        db, category_db, tenant=x_current_tenant
    )
    return category_response


@router.get(
    "/{category_id}/child",
    status_code=status.HTTP_200_OK,
    response_model=List[SubCategoriesOutSchema],
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get list of child categories ids for category with category_id.",
)
def get_child_categories(
    category_id: str = Path(..., example="Table"),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> List[SubCategoriesOutSchema]:
    fetch_category_db(db, category_id, x_current_tenant)
    root_category = category_id
    child_categories = recursive_subcategory_search(
        db, category_id, root_category, set()
    )
    response = [
        SubCategoriesOutSchema.parse_obj({"id": child_id})
        for child_id in sorted(child_categories)
    ]
    return response


# Search with params, return paginate obj, each entity
# requires children/parents
@router.post(
    "/search",
    status_code=status.HTTP_200_OK,
    response_model=Page[Union[CategoryResponseSchema, str, dict]],
    summary="Search categories.",
    response_model_exclude_none=True,
)
def search_categories(
    request: CategoryFilter,
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> Page[Union[CategoryResponseSchema, str, dict]]:
    """
    Searches and returns categories data according to search request parameters
    filters. Supports pagination and ordering.
    """
    try:
        task_response = filter_category_db(db, request, x_current_tenant)
    except BadFilterFormat as error:
        raise HTTPException(
            status_code=400,
            detail=f"{error}",
        )
    return task_response


@router.put(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=CategoryResponseSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
    },
    summary="Update category.",
)
def update_category(
    query: CategoryBaseSchema,
    category_id: str = Path(..., example="1"),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
) -> CategoryResponseSchema:
    """
    Updates category by id and returns updated category.
    """
    category_db = update_category_db(
        db, category_id, query.dict(), x_current_tenant
    )
    if not category_db:
        raise NoSuchCategoryError("Cannot update category parameters")
    link_category_with_taxonomy(
        category_db=category_db,
        x_current_tenant=x_current_tenant,
        token=token,
    )
    return response_object_from_db(category_db)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Delete category by id.",
)
def delete_category(
    category_id: str = Path(..., example="1"),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
) -> Response:
    delete_taxonomy_link(category_id, x_current_tenant, token)
    delete_category_db(db, category_id, x_current_tenant)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
