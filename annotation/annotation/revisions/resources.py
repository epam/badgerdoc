from typing import List

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from starlette import status

from annotation.database import get_db
from annotation.microservice_communication.search import (
    X_CURRENT_TENANT_HEADER,
)
from annotation.models import AnnotatedDoc
from annotation.schemas import AnnotatedDocSchema, ConnectionErrorSchema
from annotation.tags import ANNOTATION_TAG, REVISION_TAG

router = APIRouter(
    prefix="/revisions",
    tags=[REVISION_TAG, ANNOTATION_TAG],
    responses={500: {"model": ConnectionErrorSchema}},
)


@router.get(
    "/{job_id}/{file_id}",
    status_code=status.HTTP_200_OK,
    response_model=List[AnnotatedDocSchema],
    summary="Get list of all revisions for provided job_id "
    "and file_id without annotation of pages.",
)
def get_revisions_without_annotation(
    job_id: int = Path(..., examples=[1]),
    file_id: int = Path(..., examples=[1]),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
):
    revisions = (
        db.query(AnnotatedDoc)
        .filter(
            AnnotatedDoc.job_id == job_id,
            AnnotatedDoc.file_id == file_id,
            AnnotatedDoc.tenant == x_current_tenant,
        )
        .order_by(AnnotatedDoc.date)
        .all()
    )
    return revisions or []
