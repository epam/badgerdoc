from typing import Dict, Optional, Tuple

import fastapi.responses
import minio
import sqlalchemy.orm
import urllib3.exceptions

from src import db, schemas, utils
from src.config import settings

router = fastapi.APIRouter(tags=["minio"])


@router.get(
    "/download", name="gets file from minio with original content-type"
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
    storage: minio.Minio = fastapi.Depends(utils.minio_utils.get_storage),
) -> fastapi.responses.StreamingResponse:
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
    utils.minio_utils.check_bucket(f.bucket, storage)
    response = utils.minio_utils.stream_minio(f.path, f.bucket, storage)
    if original:
        response = utils.minio_utils.stream_minio(
            f.origin_path, f.bucket, storage
        )
    background_tasks.add_task(utils.minio_utils.close_conn, response)
    return fastapi.responses.StreamingResponse(
        response.stream(), media_type=response.headers["Content-Type"]
    )


@router.get(
    "/download/thumbnail", name="get thumbnail of original file in jpg format"
)
async def get_preview_from_minio(
    file_id: int,
    background_tasks: fastapi.BackgroundTasks,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    storage: minio.Minio = fastapi.Depends(utils.minio_utils.get_storage),
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
    utils.minio_utils.check_bucket(f.bucket, storage)
    if not utils.minio_utils.check_file_exist(f.thumb_path, f.bucket, storage):
        utils.minio_utils.remake_thumbnail(f, storage)
    response = utils.minio_utils.stream_minio(f.thumb_path, f.bucket, storage)
    background_tasks.add_task(utils.minio_utils.close_conn, response)
    return fastapi.responses.StreamingResponse(
        response.stream(), media_type=response.headers["Content-Type"]
    )


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
    storage: minio.Minio = fastapi.Depends(utils.minio_utils.get_storage),
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
    if not utils.minio_utils.check_file_exist(piece_path, f.bucket, storage):
        utils.minio_utils.make_pdf_piece(
            f, page_number, bbox, piece_path, storage
        )

    response = utils.minio_utils.stream_minio(piece_path, f.bucket, storage)
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
    storage: minio.Minio = fastapi.Depends(utils.minio_utils.get_storage),
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
    if settings.s3_prefix:
        bucket.name = f"{settings.s3_prefix}-{bucket.name}"
    try:
        if storage.bucket_exists(bucket.name):
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_400_BAD_REQUEST,
                detail=f"Bucket with name {bucket.name} already exists!",
            )
        storage.make_bucket(bucket.name)
    except urllib3.exceptions.MaxRetryError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except (ValueError, minio.S3Error) as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return {"detail": f"Bucket {bucket.name} successfully created!"}
