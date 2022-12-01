from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from filter_lib import Page
from sqlalchemy.orm import Session
from sqlalchemy_filters.exceptions import BadFilterFormat

from app.database import get_db
from app.errors import NoTaxonError
from app.filters import TaxonFilter
from app.microservice_communication.search import X_CURRENT_TENANT_HEADER
from app.schemas import (
    BadRequestErrorSchema,
    ConnectionErrorSchema,
    NotFoundErrorSchema,
    TaxonBaseSchema,
    TaxonInputSchema,
    TaxonResponseSchema,
)
from app.tags import TAXON_TAG
from app.taxon.services import (
    add_taxon_db,
    delete_taxon_db,
    fetch_taxon_db,
    filter_taxons,
    insert_taxon_tree,
    update_taxon_db,
)

router = APIRouter(
    prefix="/taxons",
    tags=[TAXON_TAG],
    responses={500: {"model": ConnectionErrorSchema}},
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TaxonResponseSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Save new taxon and return saved one.",
)
def save_taxon(
    taxon: TaxonInputSchema,
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> TaxonResponseSchema:
    taxon_db = add_taxon_db(db, taxon, x_current_tenant)
    return TaxonResponseSchema.from_orm(taxon_db)


@router.get(
    "/{taxon_id}",
    status_code=status.HTTP_200_OK,
    response_model=TaxonResponseSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get taxon by id.",
)
def fetch_taxon(
    taxon_id: str = Path(..., example="1"),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> TaxonResponseSchema:
    taxon_db = fetch_taxon_db(db, taxon_id, x_current_tenant)
    taxon_response = insert_taxon_tree(db, taxon_db, x_current_tenant)
    return taxon_response


@router.post(
    "/search",
    status_code=status.HTTP_200_OK,
    response_model=Page[Union[TaxonResponseSchema, str, dict]],
    summary="Search taxons.",
)
def search_categories(
    request: TaxonFilter,
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> Page[Union[TaxonResponseSchema, str, dict]]:
    """
    Searches and returns taxons data according to search request parameters
    filters. Supports pagination and ordering.
    """
    try:
        response = filter_taxons(db, request, x_current_tenant)
    except BadFilterFormat as error:
        raise HTTPException(
            status_code=400,
            detail=f"{error}",
        )
    return response


@router.put(
    "/{taxon_id}",
    status_code=status.HTTP_200_OK,
    response_model=TaxonResponseSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
    },
    summary="Update taxon.",
    response_model_exclude_none=True,
)
def update_taxon(
    query: TaxonBaseSchema,
    taxon_id: str = Path(..., example="1"),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> TaxonResponseSchema:
    """
    Updates taxon by id and returns updated taxon.
    """
    taxon_db = update_taxon_db(db, taxon_id, query.dict(), x_current_tenant)
    if not taxon_id:
        raise NoTaxonError("Cannot update taxon parameters")
    return TaxonResponseSchema.from_orm(taxon_db)


@router.delete(
    "/{taxon_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Delete taxon by id.",
)
def delete_taxon(
    taxon_id: str = Path(..., example="1"),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> Response:
    delete_taxon_db(db, taxon_id, x_current_tenant)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
