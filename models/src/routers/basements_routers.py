import logging
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from filter_lib import (
    Page,
    create_filter_model,
    form_query,
    map_request_to_filter,
    paginate,
)
from sqlalchemy.orm import Session
from tenant_dependency import TenantData

from src import crud, schemas
from src.db import Basement, get_db
from src.routers import tenant
from src.utils import (
    NoSuchTenant,
    convert_bucket_name_if_s3prefix,
    get_minio_resource,
    upload_to_object_storage,
)

LOGGER = logging.getLogger(name="models")

BasementFilterModel = create_filter_model(Basement)

router = APIRouter(prefix="/basements", tags=["basements"])


@router.post(
    "/create",
    status_code=201,
    responses={
        201: {
            "model": schemas.Basement,
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
        409: {
            "model": schemas.WrongResponse,
            "description": "Such id already exists",
        },
    },
)
def create_new_basement(
    request: schemas.BasementBase,
    session: Session = Depends(get_db),
    token: TenantData = Depends(tenant),
    x_current_tenant: str = Header(None),
) -> Basement:
    if not x_current_tenant:
        LOGGER.info("Create_new_basement doesn't get header")
        raise HTTPException(
            status_code=400, detail="Header x-current-tenant is required"
        )
    if crud.is_id_existing(session, Basement, request.id):
        LOGGER.info(
            "Create_new_basement get already existing basement id %s",
            request.id,
        )
        raise HTTPException(status_code=409, detail="Id has to be unique name")

    LOGGER.info("Creating new basement")
    basement = crud.create_instance(
        session, Basement, request, token.user_id, x_current_tenant
    )
    return basement


@router.post(
    "/search",
    response_model=Union[Page[schemas.Basement], Page[Any]],  # type: ignore
)
def search_basements(
    request: BasementFilterModel,  # type: ignore
    session: Session = Depends(get_db),
) -> Union[Page[schemas.Basement], Page[Any]]:
    query = session.query(Basement)
    filter_args = map_request_to_filter(
        request.dict(),  # type: ignore
        "Basement",
    )
    query, pagination = form_query(filter_args, query)
    return paginate([x for x in query], pagination)


@router.get(
    "/{basements_id}",
    responses={
        200: {
            "model": schemas.Basement,
            "description": "Basement by id",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Docker image was not found",
        },
    },
)
def get_basement_by_id(
    basement_id: str, session: Session = Depends(get_db)
) -> Basement:
    query = crud.get_instance(session, Basement, basement_id)
    if not query:
        LOGGER.error("Get_basement_by_id get not existing id %s", basement_id)
        raise HTTPException(status_code=404, detail="Not existing basement")
    return query


@router.put(
    "/update",
    responses={
        200: {
            "model": schemas.Basement,
            "description": "Successfully modified",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Docker image was not found",
        },
    },
)
def update_basement(
    request: schemas.BasementBase, session: Session = Depends(get_db)
) -> Basement:
    basement = crud.get_instance(session, Basement, request.id)
    if not basement:
        LOGGER.info("Update_basement get not existing id %s", request.id)
        raise HTTPException(status_code=404, detail="Not existing basement")

    modified_basement = crud.modify_instance(session, basement, request)
    LOGGER.info("basement %s was updated", request.id)
    return modified_basement


@router.delete(
    "/delete",
    responses={
        200: {
            "model": schemas.MsgResponse,
            "description": "Successfully deleted",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Docker image was not found",
        },
    },
)
def delete_basement_by_id(
    request: schemas.BasementDelete, session: Session = Depends(get_db)
) -> Dict[str, str]:
    basement = crud.get_instance(session, Basement, request.id)
    if not basement:
        LOGGER.info("Delete_basement get not existing id %s", request.id)
        raise HTTPException(status_code=404, detail="Not existing basement")
    s3_resource = get_minio_resource(tenant=basement.tenant)
    if basement.key_script:
        s3_resource.meta.client.delete_object(
            Bucket=basement.tenant, Key=basement.key_script
        )
    if basement.key_archive:
        s3_resource.meta.client.delete_object(
            Bucket=basement.tenant, Key=basement.key_archive
        )
    crud.delete_instance(session, basement)
    LOGGER.info("basement %s was deleted", request.id)
    return {"msg": "Basement was deleted"}


@router.put(
    "/{basements_id}/files",
    status_code=204,
    responses={
        404: {
            "model": schemas.WrongResponse,
            "description": "Basement does not exist",
        },
    },
)
def upload_files_to_object_storage(
    basement_id: str,
    session: Session = Depends(get_db),
    x_current_tenant: str = Header(..., alias="X-Current-Tenant"),
    script: Optional[UploadFile] = File(None),
    archive: Optional[UploadFile] = File(None),
) -> None:
    bucket_name = convert_bucket_name_if_s3prefix(x_current_tenant)
    basement = crud.get_instance(session, Basement, basement_id)
    if not basement:
        LOGGER.info(
            "upload_script_to_minio got not existing id %s", basement_id
        )
        raise HTTPException(status_code=404, detail="Not existing basement")
    try:
        s3_resource = get_minio_resource(tenant=bucket_name)
    except NoSuchTenant as err:
        LOGGER.exception(
            "Bucket %s does not exist",
            bucket_name,
        )
        raise HTTPException(status_code=500, detail=str(err))
    script_key = None
    archive_key = None
    if script:
        script_key = f"basements/{basement_id}/training_script.py"
        upload_to_object_storage(
            s3_resource=s3_resource,
            bucket_name=bucket_name,
            file=script,
            file_path=script_key,
        )
    if archive:
        archive_key = f"basements/{basement_id}/training_archive.zip"
        upload_to_object_storage(
            s3_resource=s3_resource,
            bucket_name=bucket_name,
            file=archive,
            file_path=archive_key,
        )
    crud.update_files_keys(session, basement, script_key, archive_key)
    LOGGER.info("basement %s was updated", basement_id)
