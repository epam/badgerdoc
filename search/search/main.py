import os
import asyncio
from typing import Optional

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from botocore.exceptions import BotoCoreError
from elasticsearch.exceptions import ElasticsearchException
from tenant_dependency import TenantData, get_tenant_info

import search.es as es
import search.harvester as harvester
import search.kafka_listener as kafka_listener
import search.schemas as schemas
from search.config import settings

tags = [
    {
        "name": "Search",
        "description": "Actions associated with search management.",
    },
]

TOKEN = get_tenant_info(
    url=settings.keycloak_url, algorithm=settings.jwt_algorithm
)

app = fastapi.FastAPI(
    title=settings.app_title,
    version=settings.version,
    openapi_tags=tags,
    root_path=settings.root_path,
    dependencies=[fastapi.Depends(TOKEN)],
)


if WEB_CORS := os.getenv("WEB_CORS", ""):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=WEB_CORS.split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def start_kafka_listener():
    await kafka_listener.create_topic()
    asyncio.create_task(kafka_listener.consume())


@app.on_event("shutdown")
async def app_shutdown():
    await es.ES.close()


@app.exception_handler(es.NoSuchTenant)
def minio_no_such_bucket_error(request: fastapi.Request, exc: es.NoSuchTenant):
    return fastapi.responses.JSONResponse(
        status_code=404,
        content={"detail": exc.message},
    )


@app.exception_handler(ElasticsearchException)
def elastic_exception_handler_es_error(
    request: fastapi.Request, exc: ElasticsearchException
):
    return fastapi.responses.JSONResponse(
        status_code=500,
        content={"detail": f"Error: connection error ({exc})"},
    )


@app.exception_handler(BotoCoreError)
def minio_exception_handler_bc_error(
    request: fastapi.Request, exc: BotoCoreError
):
    return fastapi.responses.JSONResponse(
        status_code=500,
        content={"detail": f"Error: connection error ({exc})"},
    )


@app.exception_handler(es.NoCategory)
def no_category_handler(request: fastapi.Request, exc: es.NoCategory):
    return fastapi.responses.JSONResponse(
        status_code=500, content={"detail": exc.message}
    )


@app.get(
    f"{settings.text_pieces_path}",
    response_model=schemas.pieces.SearchResultSchema,
    status_code=fastapi.status.HTTP_200_OK,
    tags=["Search"],
    summary="Search text pieces.",
    responses={
        404: {"model": schemas.errors.NotFoundErrorSchema},
        500: {"model": schemas.errors.ConnectionErrorSchema},
    },
)
async def get_text_piece(
    x_current_tenant: str = fastapi.Header(..., example="badger-doc"),
    token: TenantData = fastapi.Depends(TOKEN),
    category: Optional[str] = fastapi.Query(None, example="Header"),
    content: Optional[str] = fastapi.Query(None, example="Elasticsearch"),
    document_id: Optional[int] = fastapi.Query(None, ge=1, example=1),
    page_number: Optional[int] = fastapi.Query(None, ge=1, example=1),
    page_size: Optional[int] = fastapi.Query(50, ge=1, le=100, example=50),
    page_num: Optional[int] = fastapi.Query(1, ge=1, example=1),
) -> schemas.pieces.SearchResultSchema:
    """
    Searches for text pieces saved in Elastic Search according to query
    parameters. If no parameters specified - returns all text pieces from
    Elastic Search index. Supports pagination.
    """
    search_params = {}
    for param_name, param in zip(
        ("category", "content", "document_id", "page_number"),
        (category, content, document_id, page_number),
    ):
        if param:
            search_params[param_name] = param
    result = await es.search(
        es.ES,
        x_current_tenant,
        search_params,
        page_size,
        page_num,
        token.token,
    )
    return schemas.pieces.SearchResultSchema.parse_obj(result)


@app.post(
    f"{settings.text_pieces_path}",
    response_model=schemas.pieces.SearchResultSchema2,
    status_code=fastapi.status.HTTP_200_OK,
    tags=["Search"],
    summary="Search text pieces.",
    responses={
        404: {"model": schemas.errors.NotFoundErrorSchema},
        500: {"model": schemas.errors.ConnectionErrorSchema},
    },
)
async def search_text_pieces(
    request: schemas.pieces.PiecesRequest,
    x_current_tenant: str = fastapi.Header(..., example="badger-doc"),
    token: TenantData = fastapi.Depends(TOKEN),
):
    await request.adjust_categories(tenant=x_current_tenant, token=token.token)
    query = request.build_query()
    result = await es.search_v2(es.ES, x_current_tenant, query)
    return schemas.pieces.SearchResultSchema2.parse_es_response(
        result, request.pagination
    )


@app.post(
    f"{settings.indexation_path}/" + "{job_id}",
    status_code=fastapi.status.HTTP_204_NO_CONTENT,
    tags=["Search"],
    summary="Start text pieces indexation process for provided job_id.",
    responses={
        404: {"model": schemas.errors.NotFoundErrorSchema},
        500: {"model": schemas.errors.ConnectionErrorSchema},
    },
)
async def start_indexing(
    job_id: int = fastapi.Path(..., example=1),
    x_current_tenant: str = fastapi.Header(..., example="badger-doc"),
) -> fastapi.Response:
    """
    Drops all already existing text pieces from Elastic Search index for this
    job if exists and starts indexation process for new text pieces in minio
    for annotated pages mentioned in manifest.json files for this job.
    """
    await harvester.start_harvester(x_current_tenant, job_id)
    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)


@app.post(
    "/facets",
    tags=["Facets"],
    summary="API for facets",
    response_model=schemas.facets.FacetsResponse,
)
async def search_facets(
    request: schemas.facets.FacetsRequest,
    x_current_tenant: str = fastapi.Header(
        ..., example="test", alias="X-Current-Tenant"
    ),
    token: TenantData = fastapi.Depends(TOKEN),
) -> schemas.facets.FacetsResponse:
    query = request.build_es_query()
    elastic_response = await es.ES.search(index=x_current_tenant, body=query)
    response = schemas.facets.FacetsResponse.parse_es_response(
        elastic_response
    )
    await response.adjust_facet_result(x_current_tenant, token.token)
    return response
