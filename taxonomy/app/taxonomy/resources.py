from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.logging_setup import LOGGER
from app.microservice_communication.search import X_CURRENT_TENANT_HEADER
from app.schemas import (
    BadRequestErrorSchema,
    CategoryLinkSchema,
    ConnectionErrorSchema,
    JobIdSchema,
    NotFoundErrorSchema,
    TaxonomyBaseSchema,
    TaxonomyInputSchema,
    TaxonomyResponseSchema,
)
from app.tags import TAXONOMY_TAG
from app.taxonomy.services import (
    batch_latest_taxonomies,
    batch_versioned_taxonomies,
    bulk_create_relations_with_categories,
    bulk_delete_category_association,
    create_new_relation_to_job,
    create_taxonomy_instance,
    delete_taxonomy_instance,
    get_latest_taxonomy,
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
    latest_taxonomy = get_latest_taxonomy(session, taxonomy.id)
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
) -> TaxonomyResponseSchema:
    taxonomy = get_latest_taxonomy(session, taxonomy_id)
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
) -> TaxonomyResponseSchema:
    taxonomy = get_taxonomy(session, (taxonomy_id, version))
    if not taxonomy:
        LOGGER.error(
            "get_taxonomy_by_id_and_version get not existing combination"
            "of id %s and version %s",
            (taxonomy_id, version),
        )
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    return TaxonomyResponseSchema.from_orm(taxonomy)


@router.post(
    "/{taxonomy_id}/link_to_job",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Save new taxonomy and return saved one.",
)
def associate_taxonomy_to_job(
    query: JobIdSchema,
    taxonomy_id: str = Path(..., example="1"),
    session: Session = Depends(get_db),
):
    taxonomy = get_latest_taxonomy(session, taxonomy_id)
    if not taxonomy:
        LOGGER.error(
            "associate_taxonomy_to_job get not existing id %s", taxonomy_id
        )
        raise HTTPException(status_code=404, detail="Not existing taxonomy")

    # todo validate job existence.
    create_new_relation_to_job(session, taxonomy, query.id)


@router.post(
    "/link_category",
    status_code=status.HTTP_201_CREATED,
    response_model=List[CategoryLinkSchema],
    responses={
        400: {"model": BadRequestErrorSchema},
    },
    summary="Creates association between taxonomy and category.",
)
def associate_taxonomy_to_category(
    category_links: List[CategoryLinkSchema],
    session: Session = Depends(get_db),
) -> List[CategoryLinkSchema]:
    versions = []
    latests = []

    for category_link in category_links:
        if category_link.taxonomy_version:
            versions.append(category_link)
        else:
            latests.append(category_link)

    taxonomies: dict = batch_versioned_taxonomies(session, versions)
    taxonomies.update(batch_latest_taxonomies(session, latests))

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
    "/link_category/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": NotFoundErrorSchema},
    },
    summary="Deletes association between taxonomy and category.",
)
def delete_category_link(
    category_id: str = Path(..., example="1"),
    session: Session = Depends(get_db),
) -> Response:
    bulk_delete_category_association(session, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=List[TaxonomyResponseSchema],
    summary="Get all taxonomies by job id",
)
def get_job_taxonomies(
    job_id: str,
    session: Session = Depends(get_db),
):
    taxonomies = get_taxonomies_by_job_id(session, job_id)
    return [
        TaxonomyResponseSchema.from_orm(taxonomy) for taxonomy in taxonomies
    ]


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
) -> TaxonomyResponseSchema:
    """
    Updates taxonomy by id and returns updated taxonomy.
    """
    taxonomy = get_latest_taxonomy(session, query.id)
    if not taxonomy:
        LOGGER.error("update_taxonomy get not existing id %s", query.id)
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    taxonomy_db = update_taxonomy_instance(
        session,
        taxonomy,
        query,
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
) -> TaxonomyResponseSchema:
    """
    Updates taxonomy by id and returns updated taxonomy.
    """
    taxonomy = get_taxonomy(session, (taxonomy_id, version))
    if not taxonomy:
        LOGGER.error(
            "get_taxonomy_by_id_and_version get not existing combination"
            "of id %s and version %s",
            (taxonomy_id, version),
        )
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    taxonomy_db = update_taxonomy_instance(
        session,
        taxonomy,
        query,
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
) -> Response:
    taxonomy = get_latest_taxonomy(session, taxonomy_id)
    if not taxonomy:
        LOGGER.error("update_taxonomy get not existing id %s", taxonomy_id)
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    if taxonomy.latest:
        second_latest_model = get_second_latest_taxonomy(session, taxonomy_id)
        if second_latest_model is not None:
            second_latest_model.latest = True
    delete_taxonomy_instance(session, taxonomy)
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
) -> Response:
    taxonomy = get_taxonomy(session, (taxonomy_id, version))
    if not taxonomy:
        LOGGER.error(
            "delete_taxonomy_by_id_and_version get not existing combination"
            "of id %s and version %s",
            (taxonomy_id, version),
        )
        raise HTTPException(status_code=404, detail="Not existing taxonomy")
    if taxonomy.latest:
        second_latest_model = get_second_latest_taxonomy(session, taxonomy_id)
        if second_latest_model is not None:
            second_latest_model.latest = True
    delete_taxonomy_instance(session, taxonomy)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
