import logging
from typing import Any, Dict, Union

from fastapi import APIRouter, Depends, Header, HTTPException, Path
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
from src.crud import get_latest_model, get_second_latest_model
from src.db import Basement, Model, Training, get_db
from src.routers import tenant

LOGGER = logging.getLogger(name="models")

ModelFilterModel = create_filter_model(Model)
router = APIRouter(prefix="/models", tags=["models"])


@router.post(
    "/create",
    status_code=201,
    response_model=schemas.Model,
    description="Successfully created",
    responses={
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
def create_new_model(
    request: schemas.ModelWithId,
    session: Session = Depends(get_db),
    token: TenantData = Depends(tenant),
    x_current_tenant: str = Header(None),
) -> schemas.Model:
    if not x_current_tenant:
        LOGGER.info("Create_new_model doesn't get header")
        raise HTTPException(
            status_code=400, detail="Header x-current-tenant is required"
        )

    if not crud.is_id_existing(session, Basement, request.basement):
        LOGGER.info(
            "Create_new_model get not existing basement id %s",
            request.basement,
        )
        raise HTTPException(status_code=404, detail="Not existing basement")

    if request.training_id and not crud.is_id_existing(
        session, Training, request.training_id
    ):
        LOGGER.info(
            "Create_new_model get not existing training id %s",
            request.training_id,
        )
        raise HTTPException(status_code=404, detail="Not existing training")
    latest_model = get_latest_model(session, request.id)
    if latest_model:
        LOGGER.info(
            "Create_new_model find model with id %s. "
            "Setting latest field of this model to False",
            latest_model.id,
        )
        latest_model.latest = False
        new_model_version = latest_model.version + 1
        LOGGER.info("New version of model will be %d", new_model_version)
    else:
        LOGGER.info(
            "Create_new_model does not find any model with id %s. "
            "First version of model will be 1",
            request.id,
        )
        new_model_version = 1
    LOGGER.info("Creating new model")
    new_model = crud.create_instance(
        session,
        Model,
        request,
        token.user_id,
        x_current_tenant,
        {"version": new_model_version, "latest": True},
    )
    return schemas.Model.from_orm(new_model)


@router.post(
    "/search",
    response_model=Union[Page[schemas.Model], Page[Any]],  # type: ignore
)
def search_models(
    request: ModelFilterModel,  # type: ignore
    session: Session = Depends(get_db),
) -> Union[Page[schemas.Model], Page[Any]]:
    query = session.query(Model)
    filter_args = map_request_to_filter(
        request.dict(), "Model"  # type: ignore
    )
    query, pagination = form_query(filter_args, query)
    return paginate([x for x in query], pagination)


@router.get(
    "/{models_id}",
    responses={
        200: {
            "model": schemas.Model,
            "description": "Model by id",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Model was not found",
        },
    },
)
def get_model_by_id(
    model_id: str, session: Session = Depends(get_db)
) -> Model:
    query = crud.get_latest_model(session, model_id)
    if not query:
        LOGGER.error("Get_model_by_id get not existing id %s", model_id)
        raise HTTPException(status_code=404, detail="Not existing model")
    return query


@router.get(
    "/{model_id}/{version}",
    status_code=200,
    response_model=schemas.Model,
    description="Get model by id and version",
    responses={
        404: {
            "model": schemas.WrongResponse,
            "description": "Model was not found",
        },
    },
)
def get_model_by_id_and_version(
    model_id: str = Path(..., example="custom"),
    version: int = Path(..., example=1),
    session: Session = Depends(get_db),
) -> schemas.Model:
    model = crud.get_instance(session, Model, (model_id, version))
    if not model:
        LOGGER.error(
            "Get_model_by_id get not existing model with "
            "id: %s, version: %d",
            model_id,
            version,
        )
        raise HTTPException(status_code=404, detail="Not existing model")
    return schemas.Model.from_orm(model)


@router.put(
    "/update",
    responses={
        200: {
            "model": schemas.Model,
            "description": "Successfully modified",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Model or foreign keys were not found",
        },
        409: {
            "model": schemas.WrongResponse,
            "description": "Such name already exists",
        },
    },
)
def update_model(
    request: schemas.ModelWithId, session: Session = Depends(get_db)
) -> Model:
    model = crud.get_latest_model(session, request.id)
    if not model:
        LOGGER.info("Update_model get not existing id %s", request.id)
        raise HTTPException(status_code=404, detail="Not existing model")

    if not crud.is_id_existing(session, Basement, request.basement):
        LOGGER.info(
            "Update_model get not existing basement id %s",
            request.basement,
        )
        raise HTTPException(status_code=404, detail="Not existing basement")

    if request.training_id and not crud.is_id_existing(
        session, Training, request.training_id
    ):
        LOGGER.info(
            "Update_model get not existing training id %s", request.training_id
        )
        raise HTTPException(status_code=404, detail="Not existing training")

    modified_model = crud.modify_instance(session, model, request)
    LOGGER.info("Model %s was updated", request.id)
    return modified_model


@router.put(
    "/{model_id}/{version}",
    response_model=schemas.Model,
    description="Successfully modified",
    responses={
        404: {
            "model": schemas.WrongResponse,
            "description": "Model or foreign keys were not found",
        },
        409: {
            "model": schemas.WrongResponse,
            "description": "Such name already exists",
        },
    },
)
def update_model_by_id_and_version(
    request: schemas.ModelBase,
    model_id: str = Path(..., example="custom"),
    version: int = Path(..., example=1),
    session: Session = Depends(get_db),
) -> schemas.Model:
    model = crud.get_instance(session, Model, (model_id, version))
    if not model:
        LOGGER.info(
            "Update_model get not existing model with " "id: %s, version: %d",
            model_id,
            version,
        )
        raise HTTPException(status_code=404, detail="Not existing model")

    if not crud.is_id_existing(session, Basement, request.basement):
        LOGGER.info(
            "Update_model get not existing basement id %s",
            request.basement,
        )
        raise HTTPException(status_code=404, detail="Not existing basement")

    if request.training_id and not crud.is_id_existing(
        session, Training, request.training_id
    ):
        LOGGER.info(
            "Update_model get not existing training id %s", request.training_id
        )
        raise HTTPException(status_code=404, detail="Not existing training")

    modified_model = crud.modify_instance(session, model, request)
    LOGGER.info("Model %s with version %d was updated", model_id, version)
    return schemas.Model.from_orm(modified_model)


@router.delete(
    "/delete",
    responses={
        200: {
            "model": schemas.MsgResponse,
            "description": "Successfully deleted",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Model was not found",
        },
    },
)
def delete_model_by_id(
    request: schemas.ModelId, session: Session = Depends(get_db)
) -> Dict[str, str]:
    model = crud.get_latest_model(session, request.id)
    if not model:
        LOGGER.info("Delete_model get not existing id %s", request.id)
        raise HTTPException(status_code=404, detail="Not existing model")
    if model.latest:
        second_latest_model = get_second_latest_model(session, request.id)
        if second_latest_model:
            second_latest_model.latest = True
    crud.delete_instance(session, model)
    LOGGER.info("Model %s was deleted", request.id)
    return {"msg": "Model was deleted"}


@router.delete(
    "/{model_id}/{version}",
    responses={
        200: {
            "model": schemas.MsgResponse,
            "description": "Successfully deleted",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Model was not found",
        },
    },
)
def delete_model_by_id_and_version(
    model_id: str = Path(..., example="custom"),
    version: int = Path(..., example=1),
    session: Session = Depends(get_db),
) -> Dict[str, str]:
    model = crud.get_instance(session, Model, (model_id, version))
    if not model:
        LOGGER.info(
            "Delete_model get not existing model with " "id: %s, version: %d",
            model_id,
            version,
        )
        raise HTTPException(status_code=404, detail="Not existing model")
    if model.latest:
        second_latest_model = get_second_latest_model(session, model_id)
        if second_latest_model:
            second_latest_model.latest = True
    crud.delete_instance(session, model)
    LOGGER.info("Model %s with version %d was deleted", model_id, version)
    return {"msg": "Model was deleted"}


@router.post(
    "/deploy",
    status_code=201,
    responses={
        201: {
            "model": schemas.MsgResponse,
            "description": "Accepted",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Model was not found",
        },
        409: {
            "model": schemas.WrongResponse,
            "description": "Already deployed",
        },
    },
)
def deploy_model(
    request: schemas.ModelId, session: Session = Depends(get_db)
) -> Dict[str, str]:
    model = crud.get_latest_model(session, request.id)
    if not model:
        LOGGER.info("Deploy_model get not existing id %s", request.id)
        raise HTTPException(status_code=404, detail="Not existing model")
    if utils.is_model_deployed(model.id):
        crud.modify_status(
            session,
            model,
            schemas.StatusEnum.READY.value,
            schemas.StatusEnum.DEPLOYED.value,
        )
        LOGGER.info(
            "Deploy_model get id of already deployed model %s", model.id
        )
        raise HTTPException(
            status_code=409,
            detail=f"Model {model.id} has already been deployed",
        )

    LOGGER.info("Deploying model %s", model.id)
    utils.deploy(session, model)
    return {"msg": f"Model {model.id} is deploying"}


@router.post(
    "/{model_id}/{version}/deploy",
    status_code=201,
    responses={
        201: {
            "model": schemas.MsgResponse,
            "description": "Accepted",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Model was not found",
        },
        409: {
            "model": schemas.WrongResponse,
            "description": "Already deployed",
        },
    },
)
def deploy_model_by_id_and_version(
    model_id: str = Path(..., example="custom"),
    version: int = Path(..., example=1),
    session: Session = Depends(get_db),
) -> Dict[str, str]:
    model = crud.get_instance(session, Model, (model_id, version))
    if not model:
        LOGGER.info(
            "Deploy_model get not existing model with " "id: %s, version: %d",
            model_id,
            version,
        )
        raise HTTPException(status_code=404, detail="Not existing model")
    if utils.is_model_deployed(model.id):
        crud.modify_status(
            session,
            model,
            schemas.StatusEnum.READY.value,
            schemas.StatusEnum.DEPLOYED.value,
        )
        LOGGER.info(
            "Deploy_model get id of already deployed model %s", model.id
        )
        raise HTTPException(
            status_code=409,
            detail=f"Model {model.id} has already been deployed",
        )

    LOGGER.info(
        "Deploying model with " "id: %s, version: %d", model_id, version
    )
    utils.deploy(session, model)
    return {"msg": f"Model {model_id} with version {version} is deploying"}


@router.delete(
    "/undeploy",
    status_code=200,
    responses={
        200: {
            "model": schemas.MsgResponse,
            "description": "Successfully undeployed",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Model was not found",
        },
        409: {
            "model": schemas.WrongResponse,
            "description": "Fail to undeploy",
        },
    },
)
def undeploy_model(
    request: schemas.ModelId, session: Session = Depends(get_db)
) -> Dict[str, str]:
    model = crud.get_latest_model(session, request.id)
    if not model:
        LOGGER.info("Deploy_model get not existing id %s", request.id)
        raise HTTPException(status_code=404, detail="Not existing model")
    LOGGER.info("Undeploying model %s", model.id)
    if not utils.is_model_deployed(model.id):
        crud.modify_status(
            session,
            model,
            schemas.StatusEnum.DEPLOYED.value,
            schemas.StatusEnum.READY.value,
        )
        return {"msg": f"Model {model.id} is undeployed"}
    if utils.undeploy(session, model):
        return {"msg": f"Model {model.id} is undeployed"}
    raise HTTPException(
        status_code=409, detail=f"Failed to undeploy model {model.id}"
    )


@router.post(
    "/{model_id}/{version}/undeploy",
    status_code=200,
    responses={
        200: {
            "model": schemas.MsgResponse,
            "description": "Successfully undeployed",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Model was not found",
        },
        409: {
            "model": schemas.WrongResponse,
            "description": "Fail to undeploy",
        },
    },
)
def undeploy_model_by_id_and_version(
    model_id: str = Path(..., example="custom"),
    version: int = Path(..., example=1),
    session: Session = Depends(get_db),
) -> Dict[str, str]:
    model = crud.get_instance(session, Model, (model_id, version))
    if not model:
        LOGGER.info(
            "Undeploy_model get not existing model with "
            "id: %s, version: %d",
            model_id,
            version,
        )
        raise HTTPException(status_code=404, detail="Not existing model")
    LOGGER.info("Undeploying model %s", model.id)
    if not utils.is_model_deployed(model.id):
        crud.modify_status(
            session,
            model,
            schemas.StatusEnum.DEPLOYED.value,
            schemas.StatusEnum.READY.value,
        )
        return {"msg": f"Model {model.id} is undeployed"}
    if utils.undeploy(session, model):
        return {"msg": f"Model {model.id} is undeployed"}
    raise HTTPException(
        status_code=409,
        detail=f"Failed to undeploy model {model_id} "
        f"with version {version}",
    )
