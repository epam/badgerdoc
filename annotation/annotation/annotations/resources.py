import logging
from typing import Dict, List, Optional, Set
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session
from tenant_dependency import TenantData

from annotation.categories.services import (
    combine_categories,
    fetch_bunch_categories_db,
)
from annotation.database import get_db
from annotation.errors import NoSuchRevisionsError
from annotation.jobs.services import update_jobs_categories
from annotation.microservice_communication import jobs_communication
from annotation.microservice_communication.assets_communication import (
    get_file_path_and_bucket,
)
from annotation.microservice_communication.search import (
    X_CURRENT_TENANT_HEADER,
)
from annotation.schemas import (
    AnnotatedDocSchema,
    BadRequestErrorSchema,
    ConnectionErrorSchema,
    DocForSaveSchema,
    JobOutSchema,
    NotFoundErrorSchema,
    PageOutSchema,
    ParticularRevisionSchema,
    ValidationSchema,
)
from annotation.tags import ANNOTATION_TAG, JOBS_TAG, REVISION_TAG
from annotation.tasks import update_task_status

from ..models import AnnotatedDoc, File, Job, ManualAnnotationTask
from ..token_dependency import TOKEN
from .main import (
    LATEST,
    DuplicateAnnotationError,
    accumulate_pages_info,
    add_search_annotation_producer,
    check_null_fields,
    check_task_pages,
    construct_annotated_doc,
    construct_particular_rev_response,
    find_all_revisions_pages,
    find_latest_revision_pages,
    load_all_revisions_pages,
    load_latest_revision_pages,
)

router = APIRouter(
    prefix="/annotation",
    tags=[ANNOTATION_TAG],
    responses={500: {"model": ConnectionErrorSchema}},
)

router.add_event_handler("startup", add_search_annotation_producer)
logger = logging.getLogger(__name__)


@router.post(
    "/{task_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=AnnotatedDocSchema,
    responses={
        304: {"description": "Not Modified"},
        400: {"model": BadRequestErrorSchema},
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    summary="Save annotation by user.",
    tags=[ANNOTATION_TAG],
)
def post_annotation_by_user(
    doc: DocForSaveSchema,
    task_id: int = Path(..., example=5),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
    db: Session = Depends(get_db),
):
    """
    Saves annotated doc (annotation) by user. For first save base
    revision of given annotated doc should be null. "Pages", "validated"
    and "failed_validation_pages" arrays should not be empty at the same
    time, because there will be nothing to save. Tenant in header is the
    name of the bucket in minIO, where annotated pages will be saved.
    Path to pages from bucket (tenant) in minIO is as follows -
    annotation / {job_id} / {file_id}. Job_id and file_id are received from
    task entity by provided task_id in path. Also, by this path in minIO there
    will be manifest.json file, that will contain "pages" field with hashes
    for pages of only latest revisions, "validated"/"failed_validation_pages"
    fields with numbers of validated/failed_validation pages respectively.
    """
    if doc.user is None:
        detail = (
            "Field user should not be null, when saving annotation by user."
        )
        raise HTTPException(
            status_code=400,
            detail=detail,
        )
    check_null_fields(doc)

    task = (
        db.query(ManualAnnotationTask)
        .filter(
            ManualAnnotationTask.id == task_id,
            ManualAnnotationTask.jobs.has(tenant=x_current_tenant),
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id [{task_id}] was not found.",
        )

    if task.user_id != doc.user:
        raise HTTPException(
            status_code=400,
            detail=f"User with id [{doc.user}] does not "
            "match user_id associated with the task. "
            f"User_id associated with task: [{task.user_id}].",
        )

    if not task.is_validation and (
        doc.validated or doc.failed_validation_pages
    ):
        raise HTTPException(
            status_code=400,
            detail="This task is for annotation. "
            "There should not be any pages in "
            "validated and failed arrays. Pages in "
            f"validated: {doc.validated} "
            f"Pages in failed: {doc.failed_validation_pages}",
        )

    check_task_pages(
        doc.pages, doc.validated, doc.failed_validation_pages, set(task.pages)
    )

    if (
        doc.base_revision is not None
        and db.query(AnnotatedDoc)
        .filter(
            AnnotatedDoc.revision == doc.base_revision,
            AnnotatedDoc.job_id == task.job_id,
            AnnotatedDoc.tenant == x_current_tenant,
            AnnotatedDoc.file_id == task.file_id,
        )
        .first()
        is None
    ):
        raise HTTPException(
            status_code=404,
            detail=f"Annotated doc with revision [{doc.base_revision}], "
            f"job id [{task.job_id}], "
            f"file id [{task_id}] was not found.",
        )

    update_task_status(db, task)

    s3_file_path, s3_file_bucket = get_file_path_and_bucket(
        task.file_id, x_current_tenant, token.token
    )
    job: Job = db.query(Job).filter(Job.job_id == task.job_id).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job with provided job_id do not exists.",
        )
    filters = [
        AnnotatedDoc.job_id == task.job_id,
        AnnotatedDoc.file_id == task.file_id,
        AnnotatedDoc.tenant == x_current_tenant,
    ]
    if job.validation_type == ValidationSchema.extensive_coverage:
        filters.append(AnnotatedDoc.user.in_((task.user_id, None)))
    latest_doc = (
        db.query(AnnotatedDoc)
        .filter(*filters)
        .order_by(desc(AnnotatedDoc.date))
        .first()
    )
    is_latest = True
    if latest_doc is not None and latest_doc.revision != doc.base_revision:
        is_latest = False
        for page in doc.pages:
            if str(page.page_num) in latest_doc.pages:
                # non mvp case
                # checks if revision in provided doc is latest,
                # if rev is not latest and pages in provided doc
                # overlap with pages in latest rev in db,
                # throws an error
                raise HTTPException(
                    status_code=400,
                    detail=f"Given base revision is not latest "
                    f"and page with number {page.page_num} "
                    f"already exists in latest revision.",
                )
    try:
        new_annotated_doc = construct_annotated_doc(
            db=db,
            user_id=doc.user,
            pipeline_id=None,
            job_id=task.job_id,
            file_id=task.file_id,
            doc=doc,
            tenant=x_current_tenant,
            s3_file_path=s3_file_path,
            s3_file_bucket=s3_file_bucket,
            latest_doc=latest_doc,
            task_id=task_id,
            is_latest=is_latest,
        )
    except DuplicateAnnotationError:
        # To ensure this endpoint is idempotent, we need to return a 200 OK
        # response in case of duplication."
        logger.exception("Found duplication on resource creation")
        return Response("Not Modified", status_code=304)
    except ValueError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Cannot assign similar documents: {err}",
        ) from err
    db.commit()
    return AnnotatedDocSchema.from_orm(new_annotated_doc)


@router.post(
    "/{job_id}/{file_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=AnnotatedDocSchema,
    responses={
        304: {"description": "Not Modified"},
        400: {"model": BadRequestErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    summary="Save annotation by pipeline.",
    tags=[ANNOTATION_TAG],
)
def post_annotation_by_pipeline(
    doc: DocForSaveSchema,
    job_id: int = Path(..., example=3),
    file_id: int = Path(..., example=4),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    token: TenantData = Depends(TOKEN),
    db: Session = Depends(get_db),
):
    """
    Saves annotated doc (annotation) by pipeline. Base revision of
    given annotated doc should always be null. "Pages", "validated"
    and "failed_validation_pages" arrays should not be empty at the
    same time, because there will be nothing to save. Tenant in header
    is the name of the bucket in minIO, where annotated pages will
    be saved. Path to pages from bucket (tenant) in minIO is as follows -
    annotation / {job_id} / {file_id}. Also by this path in minIO there
    will be manifest.json file, that will contain "pages" field with hashes
    for pages of only latest revisions, "validated"/"failed_validation_pages"
    fields with numbers of validated/failed_validation pages respectively.
    """
    if doc.pipeline is None:
        raise HTTPException(
            status_code=400,
            detail="Field pipeline should not be null, "
            "when saving annotation by pipeline.",
        )

    if doc.base_revision is not None:
        raise HTTPException(
            status_code=400,
            detail="When saving annotation from pipeline, "
            "base revision should be null.",
        )

    check_null_fields(doc)

    s3_file_path, s3_file_bucket = get_file_path_and_bucket(
        file_id, x_current_tenant, token.token
    )

    latest_doc = (
        db.query(AnnotatedDoc)
        .filter(
            AnnotatedDoc.job_id == job_id,
            AnnotatedDoc.tenant == x_current_tenant,
            AnnotatedDoc.file_id == file_id,
        )
        .order_by(desc(AnnotatedDoc.date))
        .first()
    )
    # Add categories to jobs microservice for any commit to keep
    # it consistent (https://github.com/epam/badgerdoc/issues/841)
    categories = combine_categories(doc.categories, doc.pages)
    category_objects = fetch_bunch_categories_db(
        db, categories, x_current_tenant, root_parents=True
    )
    update_jobs_categories(db, job_id, category_objects)
    jobs_communication.append_job_categories(
        job_id, list(categories), x_current_tenant, token.token
    )
    try:
        new_annotated_doc = construct_annotated_doc(
            db=db,
            user_id=None,
            pipeline_id=doc.pipeline,
            job_id=job_id,
            file_id=file_id,
            doc=doc,
            tenant=x_current_tenant,
            s3_file_path=s3_file_path,
            s3_file_bucket=s3_file_bucket,
            latest_doc=latest_doc,
            task_id=None,
            is_latest=True,
        )
    except DuplicateAnnotationError:
        # To ensure this endpoint is idempotent, we need to return a 200 OK
        # response in case of duplication."
        logger.exception("Found duplication on resource creation")
        return Response("Not Modified", status_code=304)

    except ValueError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Cannot assign similar documents: {err}",
        ) from err
    db.commit()
    return AnnotatedDocSchema.from_orm(new_annotated_doc)


@router.get(
    "/{file_id}",
    status_code=status.HTTP_200_OK,
    response_model=List[JobOutSchema],
    responses={
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    summary="Get all job_ids that have annotations for the given file_id.",
    tags=[JOBS_TAG],
)
def get_jobs_by_file_id(
    file_id: int = Path(..., example=4),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
):
    db_file = (
        db.query(File)
        .filter_by(file_id=file_id, tenant=x_current_tenant)
        .first()
    )
    if not db_file:
        raise HTTPException(
            status_code=404,
            detail=f"File with file_id {file_id} wasn't found.",
        )
    jobs = (
        db.query(AnnotatedDoc.job_id, AnnotatedDoc.pipeline)
        .filter(
            AnnotatedDoc.file_id == file_id,
            AnnotatedDoc.tenant == x_current_tenant,
        )
        .distinct(AnnotatedDoc.job_id, AnnotatedDoc.pipeline)
        .all()
    )
    return [
        {"job_id": job.job_id, "is_manual": not bool(job.pipeline)}
        for job in jobs
    ]


@router.get(
    "/{job_id}/{file_id}/latest_by_user",
    status_code=status.HTTP_200_OK,
    response_model=Dict[int, List[PageOutSchema]],
    responses={
        500: {"model": ConnectionErrorSchema},
    },
    summary="Get latest revision made by particular "
    "user (or by pipeline) for particular pages.",
    tags=[REVISION_TAG, ANNOTATION_TAG],
)
def get_latest_revision_by_user(
    job_id: int = Path(..., example=3),
    file_id: int = Path(..., example=4),
    page_numbers: Set[int] = Query(..., min_items=1, ge=1, example={3, 4, 1}),
    user_id: Optional[UUID] = Query(
        None, example="1843c251-564b-4c2f-8d42-c61fdac369a1"
    ),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
):
    filters = [
        AnnotatedDoc.job_id == job_id,
        AnnotatedDoc.file_id == file_id,
        AnnotatedDoc.tenant == x_current_tenant,
    ]
    if user_id:
        filters.append(AnnotatedDoc.user == user_id)
    revisions = (
        db.query(AnnotatedDoc)
        .filter(and_(*filters))
        .order_by(AnnotatedDoc.date)
        .all()
    )
    pages = find_latest_revision_pages(revisions, page_numbers)
    if not pages:
        return {page_number: [] for page_number in page_numbers}
    load_latest_revision_pages(pages, x_current_tenant)
    return pages


@router.get(
    "/{job_id}/{file_id}/{revision}",
    status_code=status.HTTP_200_OK,
    response_model=ParticularRevisionSchema,
    responses={
        500: {"model": ConnectionErrorSchema},
    },
    summary="Get annotation for given revision."
    "Info will be accumulated from first revision up to"
    "given.",
    tags=[REVISION_TAG, ANNOTATION_TAG],
)
def get_annotations_up_to_given_revision(
    job_id: int = Path(..., example=1),
    file_id: int = Path(..., example=1),
    revision: str = Path(..., example="latest"),
    page_numbers: Set[int] = Query(None, min_items=1, ge=1, example={3, 4, 1}),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
    user_id: Optional[UUID] = Query(
        None,
        example="1843c251-564b-4c2f-8d42-c61fdac369a1",
        description="Enables filtering relevant revisions by user_id",
    ),
):
    job: Job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job with provided job_id do not exists.",
        )
    filters = [
        AnnotatedDoc.job_id == job_id,
        AnnotatedDoc.file_id == file_id,
        AnnotatedDoc.tenant == x_current_tenant,
    ]
    if user_id:
        filters.append(AnnotatedDoc.user.in_((user_id, None)))

    revisions = (
        db.query(AnnotatedDoc)
        .filter(*filters)
        .order_by(AnnotatedDoc.date.asc())
        .all()
    )

    if not revisions:
        return ParticularRevisionSchema(
            revision=None,
            user=None,
            pipeline=None,
            date=None,
            pages=[],
            validated=[],
            failed_validation_pages=[],
            links_json=[],
        )

    (
        validated,
        failed,
        annotated,
        _,
        categories,
        required_revision,
    ) = accumulate_pages_info(
        task_pages=[],
        revisions=revisions,
        stop_revision=revision,
        specific_pages=page_numbers,
        with_page_hash=True,
    )
    # if revision with given id (hash) was not found,
    # response with empty revision will be returned
    if required_revision is None:
        return ParticularRevisionSchema(
            revision=None,
            user=None,
            pipeline=None,
            date=None,
            pages=[],
            validated=[],
            failed_validation_pages=[],
            links_json=[],
        )

    required_revision.pages = annotated
    required_revision.validated = validated
    required_revision.failed_validation_pages = failed
    required_revision.categories = categories

    return construct_particular_rev_response(required_revision)


@router.get(
    "/{job_id}/{file_id}/changes/{revision}",
    status_code=status.HTTP_200_OK,
    response_model=ParticularRevisionSchema,
    responses={
        404: {"model": NotFoundErrorSchema},
        500: {"model": ConnectionErrorSchema},
    },
    summary="Get annotation for latest or particular revision.",
    tags=[REVISION_TAG, ANNOTATION_TAG],
)
def get_annotation_for_given_revision(
    job_id: int = Path(..., example=1),
    file_id: int = Path(..., example=1),
    revision: str = Path(..., example="latest"),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    db: Session = Depends(get_db),
):
    if revision == LATEST:
        latest = (
            db.query(AnnotatedDoc)
            .filter(
                AnnotatedDoc.job_id == job_id,
                AnnotatedDoc.file_id == file_id,
                AnnotatedDoc.tenant == x_current_tenant,
            )
            .order_by(AnnotatedDoc.date.desc())
            .first()
        )
    else:
        filters = [
            AnnotatedDoc.job_id == job_id,
            AnnotatedDoc.file_id == file_id,
            AnnotatedDoc.revision == revision,
            AnnotatedDoc.tenant == x_current_tenant,
        ]

        latest = db.query(AnnotatedDoc).filter(and_(*filters)).first()
    if not latest:
        raise NoSuchRevisionsError

    return construct_particular_rev_response(latest)


@router.get(
    "/{job_id}/{file_id}",
    status_code=status.HTTP_200_OK,
    response_model=Dict[int, List[PageOutSchema]],
    responses={
        500: {"model": ConnectionErrorSchema},
    },
    summary=(
        "Get all users revisions (or pipeline revision) for particular pages."
    ),
    tags=[REVISION_TAG, ANNOTATION_TAG],
)
def get_all_revisions(
    job_id: int,
    file_id: int,
    page_numbers: Set[int] = Query(..., min_items=1, ge=1),
    x_current_tenant: str = X_CURRENT_TENANT_HEADER,
    user_id: Optional[UUID] = Query(
        None,
        example="1843c251-564b-4c2f-8d42-c61fdac369a1",
        description=(
            "Required in case job validation type is extensive_coverage"
        ),
    ),
    db: Session = Depends(get_db),
):
    job: Job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job with provided job_id do not exists.",
        )
    filters = [
        AnnotatedDoc.job_id == job_id,
        AnnotatedDoc.file_id == file_id,
        AnnotatedDoc.tenant == x_current_tenant,
    ]
    if job.validation_type == ValidationSchema.extensive_coverage:
        filters.append(AnnotatedDoc.user.in_((user_id, None)))
    revisions = (
        db.query(AnnotatedDoc)
        .filter(and_(*filters))
        .order_by(AnnotatedDoc.date)
        .all()
    )
    pages = find_all_revisions_pages(revisions, page_numbers)
    if not pages:
        return {page_number: [] for page_number in page_numbers}
    load_all_revisions_pages(pages, x_current_tenant)
    return pages
