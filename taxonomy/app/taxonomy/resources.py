from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import NoTaxonomyError
from app.microservice_communication.search import X_CURRENT_TENANT_HEADER
from app.schemas import (
    BadRequestErrorSchema,
    ConnectionErrorSchema,
    NotFoundErrorSchema,
    TaxonomyBaseSchema,
    TaxonomyInputSchema,
    TaxonomyResponseSchema,
)
from app.tags import TAXONOMY_TAG

from .services import (
    add_taxonomy_db,
    fetch_taxonomy_db,
    update_taxonomy_db,
    delete_taxonomy_db,
    response_object_from_db,
)

router = APIRouter(
    prefix="/taxonomy",
    tags=[TAXONOMY_TAG],
    responses={500: {"model": ConnectionErrorSchema}},
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TaxonomyResponseSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Save new taxonomy and return saved one.",
)
def save_taxonomy(
    taxonomy: TaxonomyInputSchema,
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> TaxonomyResponseSchema:
    taxonomy_db = add_taxonomy_db(db, taxonomy, x_current_tenant)
    return response_object_from_db(taxonomy_db)


@router.get(
    "/{taxonomy_id}",
    status_code=status.HTTP_200_OK,
    response_model=TaxonomyResponseSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get taxonomy by id.",
)
def fetch_taxonomy(
    taxonomy_id: str = Path(..., example="1"),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> TaxonomyResponseSchema:
    taxonomy_db = fetch_taxonomy_db(db, taxonomy_id, x_current_tenant)
    return response_object_from_db(taxonomy_db)


@router.put(
    "/{taxonomy_id}",
    status_code=status.HTTP_200_OK,
    response_model=TaxonomyResponseSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
    },
    summary="Update taxonomy.",
)
def update_taxonomy(
    query: TaxonomyBaseSchema,
    taxonomy_id: str = Path(..., example="1"),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> TaxonomyResponseSchema:
    """
    Updates taxonomy by id and returns updated taxonomy.
    """
    taxonomy_db = update_taxonomy_db(
        db, taxonomy_id, query.dict(), x_current_tenant
    )
    if not taxonomy_id:
        raise NoTaxonomyError("Cannot update taxonomy parameters")
    return response_object_from_db(taxonomy_db)


@router.delete(
    "/{taxonomy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Delete taxonomy by id.",
)
def delete_taxonomy(
    taxonomy_id: str = Path(..., example="1"),
    db: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> Response:
    delete_taxonomy_db(db, taxonomy_id, x_current_tenant)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
