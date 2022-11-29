from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from filter_lib import Page
from sqlalchemy.orm import Session
from sqlalchemy_filters.exceptions import BadFilterFormat

from app.database import get_db
from app.errors import NoSuchCategoryError
from app.filters import CategoryFilter
from app.microservice_communication.search import X_CURRENT_TENANT_HEADER
from app.schemas import (
    BadRequestErrorSchema,
    CategoryBaseSchema,
    CategoryInputSchema,
    CategoryORMSchema,
    CategoryResponseSchema,
    ConnectionErrorSchema,
    NotFoundErrorSchema,
    SubCategoriesOutSchema,
)
from app.tags import CATEGORIES_TAG

from lib.tenants.src import TenantData
from microservice_communication.taxonomy_communication import link_category_with_taxonomy
from schemas.categories import CategoryDataAttributeNames
from app.token_dependency import TOKEN
from .services import (
    add_category_db,
    delete_category_db,
    fetch_category_db,
    filter_category_db,
    recursive_subcategory_search,
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
    if category_db.data_attributes:
        taxonomy_link_params = {}
        for data_attribute in category.data_attributes:
            for attr_name, value in data_attribute.items():
                if attr_name in (
                    CategoryDataAttributeNames.taxonomy_id.name,
                    CategoryDataAttributeNames.taxonomy_version.name,
                ):
                    taxonomy_link_params[attr_name] = value
        if taxonomy_link_params:
            if (
                CategoryDataAttributeNames.taxonomy_id.name
                not in taxonomy_link_params
            ):
                raise BadRequestErrorSchema("Taxonomy ID was not provided")
            link_category_with_taxonomy(
                category_id=category.id,
                tenant=x_current_tenant,
                token=token.token,
                **taxonomy_link_params,
            )
    category = CategoryORMSchema.from_orm(category_db).dict()
    return CategoryResponseSchema.parse_obj(category)


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
    category = CategoryORMSchema.from_orm(category_db).dict()
    return CategoryResponseSchema.parse_obj(category)


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


@router.post(
    "/search",
    status_code=status.HTTP_200_OK,
    response_model=Page[Any],  # type: ignore
    summary="Search categories.",
)
def search_categories(
    request: CategoryFilter,
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> Page[Any]:
    """
    Searches and returns categories data according to search request parameters
    filters. Supports pagination and ordering.
    """
    try:
        task_response = filter_category_db(db, request, x_current_tenant)
        return task_response
    except BadFilterFormat as error:
        raise HTTPException(
            status_code=400,
            detail=f"{error}",
        )


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
) -> CategoryResponseSchema:
    """
    Updates category by id and returns updated category.
    """
    category_db = update_category_db(
        db, category_id, query.dict(), x_current_tenant
    )
    if not category_db:
        raise NoSuchCategoryError("Cannot update category parameters")
    category = CategoryORMSchema.from_orm(category_db)
    return CategoryResponseSchema.parse_obj(category)


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
) -> Response:
    delete_category_db(db, category_id, x_current_tenant)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
