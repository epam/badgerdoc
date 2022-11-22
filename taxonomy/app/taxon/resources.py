from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import NoTaxonError
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

from .services import (
    add_taxon_db,
    fetch_taxon_db,
    insert_taxon_tree,
    update_taxon_db,
    delete_taxon_db,
    response_object_from_db
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
    return response_object_from_db(taxon_db)


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
    taxon_response = insert_taxon_tree(db, taxon_db)
    return taxon_response


@router.put(
    "/{taxon_id}",
    status_code=status.HTTP_200_OK,
    response_model=TaxonResponseSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
    },
    summary="Update taxon.",
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
    taxon_db = update_taxon_db(
        db, taxon_id, query.dict(), x_current_tenant
    )
    if not taxon_id:
        raise NoTaxonError("Cannot update taxon parameters")
    return response_object_from_db(taxon_db)


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
