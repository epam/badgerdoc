from typing import Dict, Optional, Tuple, Union

import fastapi.responses
import sqlalchemy.orm
from badgerdoc_storage import storage as bd_storage

from assets import db, schemas, utils
from assets.config import settings

router = fastapi.APIRouter(tags=["minio"])


@router.get(
    "/download",
    name="gets file from minio with original content-type",
    response_model=None,
)
async def get_from_minio(
    file_id: int,
    background_tasks: fastapi.BackgroundTasks,
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
    original: bool = False,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
) -> Union[
    fastapi.responses.StreamingResponse, fastapi.responses.RedirectResponse
]:
    """
    Takes an id file and a bucket name and returns streaming file with
    corresponding content-type.

        Args:\n
            id: int id of a file in minio
            bucket: a bucket name in minio
            original: determines file format. "false" for converted,
            and "true" for original

        Returns:\n
             Streaming file

    """
    f = db.service.get_file_by_id(session, file_id)
    if not f:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="No such file in a bucket",
        )

    path = f.origin_path if original else f.path
    url = bd_storage.get_storage(x_current_tenant).gen_signed_url(path, exp=60)
    return fastapi.responses.RedirectResponse(url=url, status_code=302)


@router.get(
    "/download/thumbnail", name="get thumbnail of original file in jpg format"
)
async def get_preview_from_minio(
    file_id: int,
    background_tasks: fastapi.BackgroundTasks,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> fastapi.responses.StreamingResponse:
    f = db.service.get_file_by_id(session, file_id)
    if not f:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="No such file in a bucket",
        )
    if not utils.minio_utils.check_file_exist(f.thumb_path, x_current_tenant):
        utils.minio_utils.remake_thumbnail(f, x_current_tenant)
    url = bd_storage.get_storage(x_current_tenant).gen_signed_url(
        f.thumb_path, exp=60
    )
    return fastapi.responses.RedirectResponse(url=url, status_code=302)


@router.get("/download/piece", name="get image content with provided bbox")
async def get_image_piece(
    background_tasks: fastapi.BackgroundTasks,
    file_id: int = fastapi.Query(..., ge=1, example=42),
    bbox: Tuple[float, float, float, float] = fastapi.Query(
        ..., example=(100, 100, 200, 200)
    ),
    page_number: int = fastapi.Query(..., ge=1, example=1),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
) -> fastapi.responses.StreamingResponse:
    f = db.service.get_file_by_id(session, file_id)
    if not f:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="No such file in a bucket",
        )
    if f.content_type != "application/pdf":
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"Content type {f.content_type} not supported",
        )
    piece_path = f"files/bbox/{f.id}/page{page_number}_bbox{bbox}_ext{settings.bbox_ext}.jpg"  # noqa
    if not utils.minio_utils.check_file_exist(piece_path, f.bucket, None):
        utils.minio_utils.make_pdf_piece(
            f, page_number, bbox, piece_path, None
        )

    response = utils.minio_utils.stream_minio(piece_path, f.bucket, None)
    background_tasks.add_task(utils.minio_utils.close_conn, response)
    return fastapi.responses.StreamingResponse(
        response.stream(), media_type=response.headers["Content-Type"]
    )


@router.post(
    "/bucket",
    status_code=fastapi.status.HTTP_201_CREATED,
    name="creates new bucket in minio",
)
async def create_bucket(
    bucket: schemas.Bucket,
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> Dict[str, str]:
    """
    Creates bucket into Minio. If bucket exists HTTPException will be
    raised with status code 400. Status code 400 will be raised as well
    if bucket name is less than 3 characters or name is invalid.

        Args:\n
            name: name for a new bucket

        Returns:\n
            result for creating bucket

        Raises:\n
            HTTPException status 400

    """
    raise NotImplementedError("This method is not supported")
