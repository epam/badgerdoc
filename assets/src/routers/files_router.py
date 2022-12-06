# flake8: noqa: F501
from typing import Any, Dict, List, Optional, Union

import fastapi
import filter_lib
import minio
import sqlalchemy.orm
import sqlalchemy_filters.exceptions

from src import db, exceptions, schemas, utils
from src.config import settings

router = fastapi.APIRouter(prefix="/files", tags=["files"])


@router.post(
    "/search",
    response_model=Union[filter_lib.Page[schemas.FileResponse], filter_lib.Page[Any]],  # type: ignore
    name="searches for files",
)
async def search_files(
    request: db.models.FileRequest,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> filter_lib.Page[schemas.FileResponse]:
    """
    Allows getting files metadata with filters, sorts and pagination.

        Args:\n
            request: a request to get files data, schema for this request
            generated automatically.

        Returns:\n
            an array of files metadata

    """
    try:
        query, pag = db.service.get_all_files_query(session, request.dict())
    except sqlalchemy_filters.exceptions.BadFilterFormat as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"Wrong params for operation. Hint: check types. Params = {e.args}",
        )
    return filter_lib.paginate([x for x in query], pag)


@router.post(
    "",
    status_code=fastapi.status.HTTP_201_CREATED,
    response_model=List[schemas.ActionResponse],
    name="uploads files into minio bucket",
)
async def upload_files(
    x_current_tenant: str = fastapi.Header(..., alias="X-Current-Tenant"),
    files: List[fastapi.UploadFile] = fastapi.File(...),
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    storage_: minio.Minio = fastapi.Depends(utils.minio_utils.get_storage),
) -> List[schemas.ActionResponse]:
    """
    Provides uploading many files. Files are form-data.
    Uploaded file goes to Minio storage with changed name and then
    from the storage metadata about these files goes to a database.

        Args:\n
            x_current_tenant: current bucket in minio
            files: list of files to be uploaded

        Returns:\n
            Array of objects, each object contains fields: file_name,
            id, action, status and message. For example:\n
            [
                {
                    "file_name": "A17_FlightPlan.pdf",
                    "id": 1,
                    "action": "upload",
                    "status": true,
                    "message": "Successfully uploaded"
              }
            ]

        Raises:\n
            HTTPException 404 code if bucket does not exist or 400 if bucket name
            less than 3 characters

    """
    if settings.s3_prefix:
        bucket_name = f"{settings.s3_prefix}-{x_current_tenant}"
    else:
        bucket_name = x_current_tenant

    utils.minio_utils.check_bucket(bucket_name, storage_)
    try:
        utils.common_utils.check_uploading_limit(files)

    except exceptions.UploadLimitExceedError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    upload_results = utils.common_utils.process_form_files(
        bucket_name, files, session, storage_
    )

    return [
        schemas.ActionResponse.parse_obj(response)
        for response in upload_results
    ]


@router.delete(
    "",
    status_code=fastapi.status.HTTP_201_CREATED,
    response_model=List[schemas.ActionResponse],
    name="removes files from minio bucket",
)
async def delete_files(
    objects: schemas.MinioObjects,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    storage: minio.Minio = fastapi.Depends(utils.minio_utils.get_storage),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> List[schemas.ActionResponse]:
    """
    Deletes objects from minio storage and then their metadata from database.
    If file does not exist in the bucket, then it will be skipped. The result for
    each file will be written into resulting dict.

        Args:\n
            bucket_name: current bucket in minio
            objects: list of object ids to be deleted

        Returns:\n
            Array of objects that contain a result for each element in objects arg

        Raises:\n
            HTTPException 404 code if bucket does not exist or 400 if bucket name
        less than 3 characters

    """
    utils.minio_utils.check_bucket(objects.bucket_name, storage)
    action = "delete"
    result: List[schemas.ActionResponse] = []

    for file_id in objects.objects:
        file = db.service.get_file_by_id(session, file_id)

        if not file:
            result.append(
                utils.common_utils.to_obj(
                    file_id, action, False, "Does not exist in the bucket"
                )
            )
            continue

        f_name = file.original_name
        minio_file_name = "files/" + str(file_id)
        f_original_ext = file.original_ext
        minio_ = utils.minio_utils.delete_one_from_minio(
            objects.bucket_name, minio_file_name, storage
        )
        minio_originals = 1
        if f_original_ext:
            minio_origin_file_name = "files/origins/" + str(file_id)
            minio_originals = utils.minio_utils.delete_one_from_minio(
                objects.bucket_name, minio_origin_file_name, storage
            )
        db_ = db.service.delete_file_from_db(session, file_id)

        if not (minio_ and db_ and minio_originals):
            result.append(
                utils.common_utils.to_obj(
                    file_id,
                    action,
                    False,
                    "Error with removing object from the storage and the db",
                )
            )
            continue

        result.append(
            utils.common_utils.to_obj(
                file_id, action, True, "Successfully deleted", f_name
            )
        )

    return result


@router.put(
    "",
    status_code=fastapi.status.HTTP_201_CREATED,
    response_model=schemas.FileResponse,
    name="updates file's data after preprocessing",
)
async def update_file(
    request: schemas.PreprocessResponse,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> schemas.FileResponse:
    file_obj = db.service.get_file_by_id(session, request.file)
    if not file_obj:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"File with id {request.file} does not exist!",
        )
    return db.service.update_file_status(request.file, request.status, session)
