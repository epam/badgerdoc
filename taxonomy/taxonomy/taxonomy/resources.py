from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from filter_lib import Page
from sqlalchemy.orm import Session
from sqlalchemy_filters.exceptions import BadFilterFormat

from taxonomy.database import get_db
from taxonomy.filters import TaxonomyFilter
from taxonomy.logging_setup import LOGGER
from taxonomy.microservice_communication.search import X_CURRENT_TENANT_HEADER
from taxonomy.schemas import (
    BadRequestErrorSchema,
    CategoryLinkSchema,
    ConnectionErrorSchema,
    JobTaxonomySchema,
    NotFoundErrorSchema,
    TaxonomyBaseSchema,
    TaxonomyInputSchema,
    TaxonomyResponseSchema,
)
from taxonomy.tags import TAXONOMY_TAG
from taxonomy.taxonomy.services import (
    batch_latest_taxonomies,
    batch_versioned_taxonomies,
    bulk_create_relations_with_categories,
    bulk_delete_category_association,
    create_taxonomy_instance,
    delete_taxonomy_instance,
    filter_taxonomies,
    get_latest_taxonomy,
    get_linked_taxonomies,
    get_second_latest_taxonomy,
    get_taxonomies_by_job_id,
    get_taxonomy,
    update_taxonomy_instance,
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
def create_new_taxonomy(
    taxonomy: TaxonomyInputSchema,
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> TaxonomyResponseSchema:
    if not x_current_tenant:
        LOGGER.info("create_new_taxonomy doesn't get header")
        raise HTTPException(
            status_code=400, detail="Header x-current-tenant is required"
        )
    latest_taxonomy = get_latest_taxonomy(
        session, taxonomy.id, x_current_tenant
    )
    if latest_taxonomy:
        LOGGER.info(
            "save_taxonomy find taxonomy with id %s. "
            "Setting latest field of this taxonomy to False",
            latest_taxonomy.id,
        )
        latest_taxonomy.latest = False
        new_taxonomy_version = latest_taxonomy.version + 1
        LOGGER.info("New version of taxonomy will be %d", new_taxonomy_version)
    else:
        LOGGER.info(
            "create_new_taxonomy does not find any taxonomy with id %s. "
            "First version of taxonomy will be 1",
            taxonomy.id,
        )
        new_taxonomy_version = 1
    taxonomy_db = create_taxonomy_instance(
        session=session,
        args=taxonomy,
        tenant=x_current_tenant,
        taxonomy_args={"version": new_taxonomy_version, "latest": True},
    )
    return TaxonomyResponseSchema.from_orm(taxonomy_db)


@router.get(
    "/{taxonomy_id}",
    status_code=status.HTTP_200_OK,
    response_model=TaxonomyResponseSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Get taxonomy by id.",
)
def get_taxonomy_by_id(
    taxonomy_id: str = Path(..., example="1"),
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> TaxonomyResponseSchema:
    if not x_current_tenant:
        LOGGER.info("get_taxonomy_by_id doesn't get header")
        raise HTTPException(
            status_code=400, detail="Header x-current-tenant is required"
        )
    taxonomy = get_latest_taxonomy(session, taxonomy_id, x_current_tenant)
    if not taxonomy:
        LOGGER.error("get_taxonomy_by_id get not existing id %s", taxonomy_id)
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    return TaxonomyResponseSchema.from_orm(taxonomy)


@router.get(
    "/{taxonomy_id}/{version}",
    status_code=200,
    responses={
        404: {
            "model": NotFoundErrorSchema,
            "description": "Taxonomy was not found",
        },
    },
    summary="Get taxonomy by id and version.",
)
def get_taxonomy_by_id_and_version(
    taxonomy_id: str = Path(..., example="1"),
    version: int = Path(..., example=1),
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> TaxonomyResponseSchema:
    if not x_current_tenant:
        LOGGER.info("get_taxonomy_by_id doesn't get header")
        raise HTTPException(
            status_code=400, detail="Header x-current-tenant is required"
        )
    taxonomy = get_taxonomy(session, (taxonomy_id, version), x_current_tenant)
    if not taxonomy:
        LOGGER.error(
            "get_taxonomy_by_id_and_version get not existing combination"
            "of id %s and version %s",
            (taxonomy_id, version),
        )
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    return TaxonomyResponseSchema.from_orm(taxonomy)


@router.post(
    "/link_category",
    status_code=status.HTTP_201_CREATED,
    response_model=List[CategoryLinkSchema],
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Creates association between taxonomy and category for exact job.",
)
def associate_taxonomy_to_category(
    category_links: List[CategoryLinkSchema],
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> List[CategoryLinkSchema]:
    versions = []
    latests = []

    for category_link in category_links:
        if category_link.taxonomy_version:
            versions.append(category_link)
        else:
            latests.append(category_link)

    taxonomies: dict = batch_versioned_taxonomies(
        session, versions, x_current_tenant
    )
    taxonomies.update(
        batch_latest_taxonomies(session, latests, x_current_tenant)
    )

    not_found_taxonomies = [
        link.taxonomy_id
        for link in versions + latests
        if link.taxonomy_id not in taxonomies
    ]
    if not_found_taxonomies:
        LOGGER.error(
            "associate_taxonomy_to_category get not existing ids %s",
            not_found_taxonomies,
        )
        raise HTTPException(
            status_code=404,
            detail="Taxonomy does not exist.",
        )

    bulk_create_relations_with_categories(session, taxonomies, category_links)
    return category_links


@router.delete(
    "/link_category/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Deletes association between taxonomies for exact job.",
)
def delete_category_link_by_job_id(
    job_id: str = Path(..., example="123"),
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> Response:
    bulk_delete_category_association(session, x_current_tenant, job_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/link_category/{job_id}/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Deletes association between taxonomy and category for exact job.",
)
def delete_category_link(
    job_id: str = Path(..., example="123"),
    category_id: str = Path(..., example="321"),
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> Response:
    bulk_delete_category_association(
        session, x_current_tenant, job_id, category_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=List[JobTaxonomySchema],
    summary="Get all taxonomies by job id",
)
def get_job_taxonomies(
    job_id: str,
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
):
    return get_taxonomies_by_job_id(session, job_id, x_current_tenant)


@router.put(
    "",
    status_code=status.HTTP_200_OK,
    response_model=TaxonomyResponseSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Update taxonomy.",
)
def update_taxonomy(
    query: TaxonomyInputSchema,
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> TaxonomyResponseSchema:
    """
    Updates taxonomy by id and returns updated taxonomy.
    """
    taxonomy = get_latest_taxonomy(session, query.id, x_current_tenant)
    if not taxonomy:
        LOGGER.error("update_taxonomy get not existing id %s", query.id)
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    taxonomy_db = update_taxonomy_instance(
        session, taxonomy, query, x_current_tenant
    )
    return TaxonomyResponseSchema.from_orm(taxonomy_db)


@router.put(
    "/{taxonomy_id}/{version}",
    status_code=status.HTTP_200_OK,
    response_model=TaxonomyResponseSchema,
    responses={
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
    },
    summary="Update taxonomy by id and version.",
)
def update_taxonomy_by_id_and_version(
    query: TaxonomyBaseSchema,
    taxonomy_id: str = Path(..., example="1"),
    version: int = Path(..., example=1),
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> TaxonomyResponseSchema:
    """
    Updates taxonomy by id and returns updated taxonomy.
    """
    taxonomy = get_taxonomy(session, (taxonomy_id, version), x_current_tenant)
    if not taxonomy:
        LOGGER.error(
            "get_taxonomy_by_id_and_version get not existing combination"
            "of id %s and version %s",
            (taxonomy_id, version),
        )
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    taxonomy_db = update_taxonomy_instance(
        session, taxonomy, query, x_current_tenant
    )
    return TaxonomyResponseSchema.from_orm(taxonomy_db)


@router.delete(
    "/{taxonomy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Delete latest taxonomy by id.",
)
def delete_taxonomy(
    taxonomy_id: str = Path(..., example="1"),
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> Response:
    taxonomy = get_latest_taxonomy(session, taxonomy_id, x_current_tenant)
    if not taxonomy:
        LOGGER.error("update_taxonomy get not existing id %s", taxonomy_id)
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    if taxonomy.latest:
        second_latest_model = get_second_latest_taxonomy(
            session, taxonomy_id, x_current_tenant
        )
        if second_latest_model is not None:
            second_latest_model.latest = True
    delete_taxonomy_instance(session, taxonomy, x_current_tenant)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{taxonomy_id}/{version}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Delete taxonomy by id and version.",
)
def delete_taxonomy_by_id_and_version(
    taxonomy_id: str = Path(..., example="1"),
    version: int = Path(..., example=1),
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> Response:
    taxonomy = get_taxonomy(session, (taxonomy_id, version), x_current_tenant)
    if not taxonomy:
        LOGGER.error(
            "delete_taxonomy_by_id_and_version get not existing combination"
            "of id %s and version %s",
            (taxonomy_id, version),
        )
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    if taxonomy.latest:
        second_latest_model = get_second_latest_taxonomy(
            session, taxonomy_id, x_current_tenant
        )
        if second_latest_model is not None:
            second_latest_model.latest = True
    delete_taxonomy_instance(session, taxonomy, x_current_tenant)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/all",
    status_code=status.HTTP_200_OK,
    response_model=Page[Union[TaxonomyResponseSchema, str, dict]],
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Search all taxonomies.",
)
def search_categories(
    request: TaxonomyFilter,
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> Page[Union[TaxonomyResponseSchema, str, dict]]:
    """
    Searches and returns taxonomies according to search request parameters
    filters. Supports pagination and ordering.
    """
    try:
        response = filter_taxonomies(session, request, x_current_tenant)
    except BadFilterFormat as error:
        raise HTTPException(
            status_code=400,
            detail=f"{error}",
        )
    return response


@router.get(
    "/link_category/{job_id}/{category_id}",
    response_model=List[TaxonomyResponseSchema],
    status_code=200,
    responses={
        404: {
            "model": NotFoundErrorSchema,
            "description": "Taxonomy was not found",
        },
    },
    summary="Get taxonomy by job id and category id.",
)
def get_taxonomy_by_job_and_category_id(
    job_id: str = Path(..., example="123"),
    category_id: str = Path(..., example="321"),
    session: Session = Depends(get_db),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
) -> List[TaxonomyResponseSchema]:
    taxonomy = get_linked_taxonomies(
        session, job_id, category_id, x_current_tenant
    )
    if not taxonomy:
        LOGGER.error(
            "get_taxonomy_by_job_and_category_id get not existing combination"
            "of id %s and version %s",
            (job_id, category_id),
        )
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    return taxonomy
