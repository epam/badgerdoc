from typing import Dict, List, Optional, Set

from fastapi import (
    Body,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session
from tenant_dependency import TenantData, get_tenant_info

from src import db, schema
from src.config import settings
from src.health_check_easy_ocr import health_check_preprocessing
from src.send_preprocess_results import send_preprocess_result
from src.tasks import GetLanguagesTask, PreprocessingTask
from src.text_merge import merge_words_to_paragraph
from src.utils.aiohttp_utils import http_session
from src.utils.logger import get_logger
from src.utils.minio_utils import convert_bucket_name_if_s3prefix
from src.utils.utils import map_finish_status_for_assets

logger = get_logger(__name__)
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    root_path=settings.root_path,
)

tenant = get_tenant_info(url=settings.keycloak_host, algorithm="RS256")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await http_session.close()


@app.post("/", response_model=schema.AnnotationData)
def run_text_matching(
    request_data: schema.AnnotationData,
) -> schema.AnnotationData:
    """Merge words into paragraphs."""
    return merge_words_to_paragraph(request_data)


@app.get(
    "/tokens/{file_id}",
    responses={
        200: {
            "model": schema.PreprocessingResultResponse,
            "description": "`!`For more information look at preprocessing microservice. "
            "This endpoint just glues it's results. "
            "https://git.epam.com/epm-uii/badgerdoc/back-end/-/tree/master/preprocessing",
        },
        400: {
            "model": schema.MinioProblem,
            "description": "Some problems with minio",
        },
    },
    summary="Get data by preprocessing result.",
)
def get_preprocessing_result(
    file_id: int = Path(..., example=4),
    pages: Optional[Set[int]] = Query(
        None, min_items=1, ge=1, example={3, 4, 1}
    ),
    current_tenant: str = Header(
        ..., example="tenant", alias="X-Current-Tenant"
    ),
) -> Response:
    """
    Take preprocess data from MinIO for `file_id`, and return it as array of pages.
    If file doesn't contain words, then service return array of pages with empty `objs` field.
    If there are no preprocess result (preprocess didn't run or `file_id` is wrong), then return `[]`.
    """
    logger.info(
        "Get request to `preprocessing_result` endpoint. With params: `file_id`=%s, `pages`=%s, `tenant`=%s",
        file_id,
        pages,
        current_tenant,
    )
    bucket_name = convert_bucket_name_if_s3prefix(current_tenant)
    return Response(
        content=send_preprocess_result(bucket_name, file_id, pages),
        media_type="application/json",
    )


@app.post(
    "/run_preprocess",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run preprocessing service via pipelines",
)
async def execute_preprocessing_service(
    run_params: schema.PreprocessExecuteRequest,
    current_tenant: str = Header(..., alias="X-Current-Tenant"),
    token_data: TenantData = Depends(tenant),
    session: Session = Depends(db.service.session_scope),
) -> Dict[str, str]:
    """Create task for preprocessing."""
    logger.info(
        "Get request to `/run_preprocess` endpoint with %s, %s",
        current_tenant,
        run_params,
    )
    task = PreprocessingTask(
        pipeline_id=run_params.pipeline_id,
        file_ids=run_params.file_ids,
        languages=run_params.languages,
        tenant=current_tenant,
        jw_token=token_data.token,
        session=session,
    )
    await task.execute()
    await task.update_file_statuses(
        run_params.file_ids,
        schema.PreprocessingStatus.PREPROCESSING_IN_PROGRESS,
        current_tenant,
        token_data.token,
    )
    return {"status": "success"}


@app.put(
    "/tasks/{task_id}",
    tags=["Preprocessing tasks"],
    status_code=status.HTTP_201_CREATED,
)
async def update_task_status(
    request: schema.UpdateStatusRequest,
    task_id: int = Path(...),
    token_data: TenantData = Depends(tenant),
    current_tenant: str = Header(..., alias="X-Current-Tenant"),
    session: Session = Depends(db.service.session_scope),
) -> Dict[str, str]:
    task: Optional[
        db.models.DbPreprocessingTask
    ] = db.service.get_task_by_execution_id(task_id, session)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such task"
        )

    db.service.update_task(task_id, request.status, session)
    finished, file_status = db.service.check_preprocessing_complete(
        task.file_id, task.batch_id, session
    )
    if finished:
        assets_status: schema.PreprocessingStatus = (
            map_finish_status_for_assets(file_status)
        )
        await PreprocessingTask.update_file_statuses(
            [task.file_id], assets_status, current_tenant, token_data.token
        )
    return {task.execution_id: task.status}


@app.get(
    "/lang",
    status_code=status.HTTP_200_OK,
    summary="Return list of available preprocessing languages.",
)
async def get_list_language(
    model_id: str = Query(..., description="model id", example="preprocessing")
) -> List[str]:
    logger.info(f"Get request to `/lang` endpoint for model_id=%s", model_id)
    return await GetLanguagesTask(model_id).execute()


@app.post(
    "/preprocessing_health_check",
    status_code=status.HTTP_200_OK,
    summary="Return `True` if test succeed, otherwise `False`",
)
async def preprocessing_health_check(
    model_url: str, languages: Optional[Set[str]] = Body(None, example=None)
) -> bool:
    """Test run for preprocessing"""
    return await health_check_preprocessing(model_url, languages)
