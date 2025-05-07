import logging
import tempfile
from datetime import datetime
from typing import Optional

import fastapi
import filter_lib
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy_filters
from badgerdoc_storage import storage as bd_storage
from pydantic import BaseModel, constr

from assets import db, schemas
from assets.db.models import ExtractionStatus

router = fastapi.APIRouter(prefix="/extractions", tags=["extractions"])

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ExtractionCreateRequest(BaseModel):
    file_id: int
    engine: constr(min_length=3, max_length=10, pattern="^[a-zA-Z]+$")  # noqa
    page_count: int
    file_extension: constr(
        min_length=1, max_length=5, pattern="^[a-zA-Z]+$"  # noqa
    )


@router.post("/upload")
async def upload_extraction(
    id: int = fastapi.Form(...),
    page_num: int = fastapi.Form(..., ge=1, le=1_000_000),
    file: fastapi.UploadFile = fastapi.File(...),
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
):
    """
    Upload endpoint for extractions.

    This function uploads extraction file into storage.
    After all pages uploaded, call `/finish`
    to finish extraction. Uploading in finished
    extractions are forbidden.

    Args:
        id: Extraction ID
        page_num: Page number
        file: Binary file to upload for the extraction
        session: Database session
        x_current_tenant: Current tenant header

    Returns:
        dict: A response indicating successful upload
    """
    extraction = db.service.get_extraction_by_id(session, id, x_current_tenant)
    if not extraction:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Extraction not found",
        )

    if extraction.status == ExtractionStatus.finished:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail="Extraction is already finished and cannot be modified",
        )

    original_filename = file.filename
    file_extension = ""
    if "." in original_filename:
        file_extension = original_filename.split(".")[-1]
    if extraction.file_extension != file_extension:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=(
                "File extension does not match the extraction "
                f"file extension. Got `{file_extension}` "
                f"expected `{extraction.file_extension}`."
            ),
        )

    page_file_path = f"{extraction.file_path}/{page_num}.{file_extension}"

    with tempfile.NamedTemporaryFile() as temp_file:
        temp_file_path = temp_file.name
        content = await file.read()
        temp_file.write(content)
        try:
            bd_storage.get_storage(x_current_tenant).upload(
                page_file_path, temp_file_path, content_type=file.content_type
            )

        except Exception:
            logger.exception("Failed to upload file to storage")
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file",
            )

    return {
        "status": "success",
        "message": f"Extraction page {page_num} uploaded successfully",
        "file_path": page_file_path,
        "id": extraction.id,
    }


@router.post("/create", status_code=201)
def create_extraction(
    request: ExtractionCreateRequest,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> dict:
    """Creates a FilesExtractions record for a file in 'started' status.

    This function initiates the extraction process by creating a new
    extraction record. After creating this record, the client must upload
    extraction pages using the '/upload' endpoint for each page. Once all
    pages are uploaded, the client must call the '/finish' endpoint to
    complete the extraction process.

    file_extension: Expected file type for all uploaded extraction files
                    (e.g., "json", "csv"). All files in this extraction
                    must have the same extension.

    Args:
        request: Contains file_id, engine (3-10 chars), and number of pages
        session: Database session
        x_current_tenant: Current tenant header

    Returns:
        FilesExtractions: Created extraction record
    """
    unique_id = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = (
        f"files/{request.file_id}/extractions/{request.engine}/{unique_id}"
    )

    file = db.service.get_file_by_id_and_tenant(
        session, request.file_id, x_current_tenant
    )
    if not file:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    try:
        extraction = db.service.create_extraction(
            session,
            file_id=request.file_id,
            engine=request.engine,
            file_path=file_path,
            page_count=request.page_count,
            file_extension=request.file_extension,
        )
    except Exception:
        logger.exception("Failed to create extraction")
        raise fastapi.HTTPException(status_code=500, detail="Database error")

    return {
        "status": "success",
        "message": "Extraction created",
        "id": extraction.id,
        "file_path": file_path,
    }


@router.post("/finish")
async def finish_extraction(
    extraction_id: int,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
):
    """
    Finish the extraction process for a given extraction ID


    Args:
        extraction_id (int): The ID of the extraction to finish.
        session: Database session
        x_current_tenant: Current tenant header

    Returns:
        dict: A response indicating successful completion.
    """
    extraction = db.service.get_extraction_by_id(
        session, extraction_id, x_current_tenant
    )
    if not extraction:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Extraction not found",
        )

    if extraction.status == ExtractionStatus.finished:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail="Extraction is already finished",
        )

    try:
        extraction = db.service.finish_extraction(session, extraction)
    except Exception:
        logger.exception("Failed to update extraction status")
        raise fastapi.HTTPException(status_code=500, detail="Database error")

    return {
        "status": "success",
        "message": "Extraction finished successfully",
        "id": extraction.id,
    }


@router.post(
    "/search",
    response_model=filter_lib.Page[schemas.ExtractionResponse],  # type: ignore
    name="Searches for extractions",
)
async def search_files(
    request: db.models.ExtractionRequest,
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
) -> filter_lib.Page[schemas.ExtractionResponse]:
    try:
        query, pag = db.service.get_all_extractions(
            session, request.dict(), x_current_tenant
        )
    except sqlalchemy_filters.exceptions.BadFilterFormat as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=(
                "Wrong params for operation. "
                f"Hint: check types. Params = {e.args}"
            ),
        )
    return filter_lib.paginate([x for x in query], pag)


@router.get(
    "/download",
    name="Get signed URL for downloading extraction file",
    response_model=None,
)
async def download(
    extraction_id: int,
    page_num: int = fastapi.Query(..., ge=1, le=1_000_000),
    x_current_tenant: Optional[str] = fastapi.Header(
        None, alias="X-Current-Tenant"
    ),
    session: sqlalchemy.orm.Session = fastapi.Depends(
        db.service.session_scope_for_dependency
    ),
) -> dict:
    """
    Generate a signed URL for downloading an extraction file.

    This function validates the extraction ID and page number, then generates
    a presigned URL for the requested extraction page and returns it along with
    the URL's validity period. Note that this function only validates the
    extraction record in the database but does not check if the file actually
    exists in storage.

    Args:
        extraction_id: ID of the extraction to download
        page_num: Page number of the extraction to download (must be within
            the extraction's page range)
        x_current_tenant: Current tenant identifier from header
        session: Database session

    Returns:
        dict: Object containing the signed URL and its validity period

    Raises:
        HTTPException 404: If the extraction is not found
        HTTPException 400: If the requested page number exceeds
                           the extraction's page count
    """
    extraction = db.service.get_extraction_by_id(
        session, extraction_id, x_current_tenant
    )
    if not extraction:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Extraction not found",
        )
    if page_num > extraction.page_count:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=(
                "Page number exceeds the number of " "pages in the extraction"
            ),
        )

    path = f"{extraction.file_path}/{page_num}.{extraction.file_extension}"
    logger.info("Downloading file from path: %s", path)

    exp = 60
    url = bd_storage.get_storage(x_current_tenant).gen_signed_url(
        path, exp=exp
    )
    return {"signed_url": url, "valid_for": exp}
