from typing import List, Optional

import fastapi
import sqlalchemy.orm
import urllib3.exceptions

from assets import db, exceptions, schemas, utils

router = fastapi.APIRouter(prefix="/s3_upload", tags=["s_3"])


@router.post(
    "",
    status_code=fastapi.status.HTTP_201_CREATED,
    response_model=List[schemas.ActionResponse],
    name="downloads files from s3",
)
def download_s3_files(
    s3_data: schemas.S3Data,
    storage_url: Optional[str] = None,
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
) -> List[schemas.ActionResponse]:
    """
    Provides uploading many files from one s3 bucket to MinIO

    Args:\n
            access_key_id: storage access key
            secret_access_key: storage secret access key
            storage_url: storage endpoint. Example: "http://localhost:9000"
            bucket_s3: s3 storage bucket name from where files to be downloaded
            files_keys: list of files keys, paths to the file in s3 storage.
            uploaded
    """
    try:
        utils.common_utils.check_uploading_limit(s3_data.files_keys)
    except exceptions.UploadLimitExceedError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    s3 = utils.s3_utils.S3Manager(
        s3_data.access_key_id, s3_data.secret_access_key, storage_url
    )
    try:
        s3.check_s3(s3_data.bucket_s3, s3_data.files_keys)

    except (exceptions.FileKeyError, exceptions.BucketError) as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except urllib3.exceptions.MaxRetryError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    bucket_name = x_current_tenant
    s3_files = s3.get_files(s3_data.bucket_s3, s3_data.files_keys)

    upload_results = utils.common_utils.process_s3_files(
        bucket_name, s3_files, session
    )

    return [
        schemas.ActionResponse.parse_obj(response)
        for response in upload_results
    ]  # noqa
