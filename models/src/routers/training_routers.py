import logging
import pathlib
import tempfile
from typing import Any, Dict, Union

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Path,
    Response,
    UploadFile,
    status,
)
from filter_lib import (
    Page,
    create_filter_model,
    form_query,
    map_request_to_filter,
    paginate,
)
from sqlalchemy.orm import Session
from tenant_dependency import TenantData

from src import crud, schemas, utils
from src.colab_ssh_utils import (
    COLAB_TRAINING_DIRECTORY,
    check_aws_credentials_file,
    connect_colab,
    local_mount_colab_drive,
    sync_colab_with_minio,
    upload_file_to_colab,
)
from src.convert_utils import prepare_dataset_info
from src.db import Basement, Training, get_db
from src.routers import tenant
from src.utils import (
    NoSuchTenant,
    convert_bucket_name_if_s3prefix,
    get_minio_object,
    get_minio_resource,
)

LOGGER = logging.getLogger(name="models")
TRAINING_SCRIPT_NAME = "training_script.py"
TRAINING_ARCHIVE_NAME = "training_archive.zip"
ANNOTATION_DATASET_NAME = "annotation_dataset.zip"

TrainingFilterModel = create_filter_model(Training)
router = APIRouter(prefix="/trainings", tags=["trainings"])


@router.post(
    "/create",
    status_code=201,
    responses={
        201: {
            "model": schemas.Training,
            "description": "Successfully created",
        },
        400: {
            "model": schemas.HeaderResponse,
            "description": "Request without header",
        },
        401: {
            "model": schemas.UnauthorisedResponse,
            "description": "Unauthorized",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Foreign key was not found",
        },
    },
)
def create_new_training(
    request: schemas.TrainingBase,
    session: Session = Depends(get_db),
    token: TenantData = Depends(tenant),
    x_current_tenant: str = Header(None),
) -> Training:
    if not x_current_tenant:
        LOGGER.info("Create_new_training doesn't get header")
        raise HTTPException(
            status_code=400, detail="Header x-current-tenant is required"
        )
    if not crud.is_id_existing(session, Basement, request.basement):
        LOGGER.info(
            "Create_new_training get not existing basement id %s",
            request.basement,
        )
        raise HTTPException(status_code=404, detail="Not existing basement")

    LOGGER.info("Creating new training")
    training = crud.create_instance(
        session, Training, request, token.user_id, x_current_tenant
    )
    return training


@router.put(
    "/{training_id}/files",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {
            "model": schemas.WrongResponse,
            "description": "Training model was not found",
        },
    },
)
def upload_files_to_object_storage(
    x_current_tenant: str = Header(..., alias="X-Current-Tenant"),
    training_id: str = Path(..., example=1),
    archive: UploadFile = File(...),
    session: Session = Depends(get_db),
) -> Response:
    training = crud.get_instance(session, Training, training_id)
    if not training:
        raise HTTPException(
            status_code=404,
            detail="Training with given id does not exist",
        )
    bucket_name = convert_bucket_name_if_s3prefix(x_current_tenant)
    s3_resource = get_minio_resource(tenant=bucket_name)
    key_archive = f"trainings/{training_id}/training_archive.zip"
    utils.upload_to_object_storage(
        s3_resource=s3_resource,
        bucket_name=bucket_name,
        file=archive,
        file_path=key_archive,
    )
    crud.update_files_keys(session, training, None, key_archive)
    LOGGER.info("Training model %s was updated", training_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/search",
    response_model=Union[Page[schemas.Training], Page[Any]],  # type: ignore
)
def search_training(
    request: TrainingFilterModel,  # type: ignore
    session: Session = Depends(get_db),
) -> Union[Page[schemas.Training], Page[Any]]:
    query = session.query(Training)
    filter_args = map_request_to_filter(
        request.dict(), "Training"  # type: ignore
    )
    query, pagination = form_query(filter_args, query)
    return paginate([x for x in query], pagination)


@router.get(
    "/{trainings_id}",
    responses={
        200: {
            "model": schemas.Training,
            "description": "Training by id",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Training was not found",
        },
    },
)
def get_training_by_id(
    training_id: int, session: Session = Depends(get_db)
) -> Training:
    query = crud.get_instance(session, Training, training_id)
    if not query:
        LOGGER.error("Get_training_by_id get not existing id %s", training_id)
        raise HTTPException(status_code=404, detail="Not existing training")
    return query


@router.put(
    "/update",
    responses={
        200: {
            "model": schemas.Training,
            "description": "Successfully modified",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Training or foreign key was not found",
        },
    },
)
def update_training(
    request: schemas.TrainingUpdate, session: Session = Depends(get_db)
) -> Training:
    training = crud.get_instance(session, Training, request.id)
    if not training:
        LOGGER.info("Update_training get not existing id %s", request.id)
        raise HTTPException(status_code=404, detail="Not existing training")

    if not crud.is_id_existing(session, Basement, request.basement):
        LOGGER.info(
            "Update_training get not existing basement id %s",
            request.basement,
        )
        raise HTTPException(status_code=404, detail="Not existing basement")

    modified_training = crud.modify_instance(session, training, request)
    LOGGER.info("Training %d was updated", request.id)
    return modified_training


@router.delete(
    "/delete",
    responses={
        200: {
            "model": schemas.MsgResponse,
            "description": "Successfully deleted",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Training was not found",
        },
    },
)
def delete_training_by_id(
    request: schemas.TrainingDelete,
    session: Session = Depends(get_db),
    x_current_tenant: str = Header(..., alias="X-Current-Tenant"),
) -> Dict[str, str]:
    training = crud.get_instance(session, Training, request.id)
    if not training:
        LOGGER.info("Delete_training get not existing id %s", request.id)
        raise HTTPException(status_code=404, detail="Not existing training")
    bucket_name = convert_bucket_name_if_s3prefix(x_current_tenant)
    try:
        s3_resource = get_minio_resource(tenant=bucket_name)
    except NoSuchTenant as err:
        LOGGER.exception(
            "Bucket %s does not exist",
            bucket_name,
        )
        raise HTTPException(status_code=500, detail=str(err))
    s3_resource.meta.client.delete_object(
        Bucket=bucket_name, Key=training.key_archive
    )
    crud.delete_instance(session, training)
    LOGGER.info("Training %d was deleted", request.id)
    return {"msg": "Training was deleted"}


@router.post(
    "/{training_id}/annotation_dataset",
    responses={
        200: {
            "model": schemas.MsgResponse,
            "description": "Dataset creation is started",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Training was not found",
        },
        500: {
            "model": schemas.ConnectionErrorResponse,
            "description": "Convert service connection error",
        },
    },
)
def prepare_annotation_dataset(
    training_id: int,
    convert_request: schemas.ConvertRequestSchema,
    session: Session = Depends(get_db),
    x_current_tenant: str = Header(..., alias="X-Current-Tenant"),
    token: TenantData = Depends(tenant),
) -> schemas.MsgResponse:
    training = crud.get_instance(session, Training, training_id)
    if not training:
        LOGGER.info("Prepare dataset get not existing id %s", training_id)
        raise HTTPException(status_code=404, detail="Not existing training")
    minio_path = prepare_dataset_info(
        convert_request, x_current_tenant, token.token
    )
    training.key_annotation_dataset = minio_path
    session.commit()
    LOGGER.info("Dataset creation for training %s is started", training_id)
    return {"msg": f"Dataset creation for training {training_id} is started"}


@router.post(
    "/{training_id}/start",
    responses={
        200: {
            "model": schemas.MsgResponse,
            "description": "Successfully started",
        },
        400: {
            "model": schemas.WrongResponse,
            "description": "Training has no training script yet",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Training was not found",
        },
        500: {
            "model": schemas.ConnectionErrorResponse,
            "description": "Connection Error",
        },
    },
)
def start_training(
    credentials: schemas.TrainingCredentials,
    training_id: int = Path(..., example=1),
    session: Session = Depends(get_db),
    token: TenantData = Depends(tenant),
    x_current_tenant: str = Header(..., example="test"),
) -> schemas.MsgResponse:
    """
    Connects to Google Colab's session with provided credentials: user,
    password, host and port. Copy training script and archive with additional
    files (if required for training) for training_id from minio storage into
    Colab's file system. Files will be located in "/content/training/"
    directory. After that starts execution of training script.
    """
    training = crud.get_instance(session, Training, training_id)
    if not training:
        LOGGER.info("Start_training get not existing id %s", training_id)
        raise HTTPException(status_code=404, detail="Not existing training")
    key_script = training.bases.key_script
    if not key_script:
        LOGGER.info("training %s has no training script yet", training_id)
        raise HTTPException(
            status_code=400,
            detail=f"Training {training_id} has no training script yet",
        )
    key_dataset = training.key_annotation_dataset
    if not key_dataset:
        LOGGER.info(
            "Annotation dataset for training %s is not prepared yet",
            training_id,
        )
        raise HTTPException(
            status_code=400,
            detail=f"Annotation dataset for training {training_id} not ready",
        )
    key_archive = training.bases.key_archive
    with connect_colab(credentials) as ssh_client:
        bucket = convert_bucket_name_if_s3prefix(x_current_tenant)
        file_script, size_script = get_minio_object(bucket, key_script)
        upload_file_to_colab(
            ssh_client, file_script, size_script, TRAINING_SCRIPT_NAME
        )
        file_dataset, size_dataset = get_minio_object(bucket, key_dataset)
        upload_file_to_colab(
            ssh_client, file_dataset, size_dataset, ANNOTATION_DATASET_NAME
        )
        if key_archive:
            file_archive, size_archive = get_minio_object(bucket, key_archive)
            upload_file_to_colab(
                ssh_client, file_archive, size_archive, TRAINING_ARCHIVE_NAME
            )
        ssh_client.exec_command(
            f"python {COLAB_TRAINING_DIRECTORY}{TRAINING_SCRIPT_NAME}"
        )
    return {"msg": f"Training with id {training_id} is started"}


@router.post(
    "/{training_id}/results",
    responses={
        200: {
            "model": schemas.MsgResponse,
            "description": "Get results files",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Training was not found",
        },
        500: {
            "model": schemas.ConnectionErrorResponse,
            "description": "Connection Error",
        },
    },
)
def download_training_results(
    credentials: schemas.TrainingCredentials,
    training_id: int = Path(..., example=1),
    session: Session = Depends(get_db),
    token: TenantData = Depends(tenant),
    x_current_tenant: str = Header(..., example="test"),
) -> schemas.MsgResponse:
    """
    Connects to Google Colab's session with provided credentials: user,
    password, host and port and copy results of training into minio storage.
    Results should be located at in "/content/training/results" directory in
    colab's file system.
    """
    bucket_name = convert_bucket_name_if_s3prefix(x_current_tenant)
    training_exists = crud.is_id_existing(session, Training, training_id)
    if not training_exists:
        LOGGER.info(
            "Download_training_results get not existing id %s", training_id
        )
        raise HTTPException(status_code=404, detail="Not existing training")
    home_directory = pathlib.Path.home()
    check_aws_credentials_file(home_directory)
    with tempfile.TemporaryDirectory(dir=home_directory) as temp_dir:
        LOGGER.info(f"Created temporary directory: {temp_dir}")
        local_mount_colab_drive(temp_dir, credentials)
        sync_colab_with_minio(temp_dir, bucket_name, training_id)
    return {"msg": f"Results for training with id {training_id} were uploaded"}
