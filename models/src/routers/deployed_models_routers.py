import logging
from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, HTTPException
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

from src import schemas, utils
from src.constants import MODELS_NAMESPACE

router = APIRouter(prefix="/deployed_models", tags=["deployed_models"])
LOGGER = logging.getLogger(name="models")


@router.get(
    "/search",
    status_code=200,
    responses={
        200: {"description": "Models list"},
    },
)
def get_deployed_model_list() -> List[schemas.DeployedModelMainData]:
    try:
        config.load_incluster_config()
    except config.ConfigException as cfg_ex:
        raise HTTPException(
            status_code=404, detail="Cluster is not running"
        ) from cfg_ex
    response = []
    api = client.CustomObjectsApi()
    models = api.list_namespaced_custom_object(
        group="serving.knative.dev",
        version="v1",
        plural="services",
        namespace=MODELS_NAMESPACE,
    )
    for model in models["items"]:
        model_data = schemas.DeployedModelMainData(
            datetime_creation=str(
                datetime.strptime(
                    model["metadata"]["creationTimestamp"],
                    "%Y-%m-%dT%H:%M:%SZ",
                )
            ),
            status=model["status"]["conditions"][0]["status"],
            name=model["metadata"]["name"],
            url=model["status"]["url"],
        )
        response.append(model_data)
    return response


@router.get(
    "/{model_name}",
    status_code=200,
    responses={
        200: {
            "model": schemas.DeployedModelDetails,
            "description": "Models by id",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Model was not found",
        },
    },
)
def get_deployed_model_by_name(
    model_name: str,
) -> schemas.DeployedModelDetails:
    try:
        config.load_incluster_config()
    except config.ConfigException as cfg_ex:
        raise HTTPException(
            status_code=404, detail="Cluster is not running"
        ) from cfg_ex
    api = client.CustomObjectsApi()
    try:
        model = api.get_namespaced_custom_object(
            group="serving.knative.dev",
            version="v1",
            plural="services",
            namespace=MODELS_NAMESPACE,
            name=model_name,
        )
    except ApiException as api_ex:
        if api_ex.status != 404:
            raise
        LOGGER.error("%s model doesn't exist", model_name)
        raise HTTPException(status_code=404, detail="Not existing model")
    metadata = model["metadata"]
    container_data = model["spec"]["template"]["spec"]["containers"][0]
    return schemas.DeployedModelDetails(
        apiVersion=model["apiVersion"],
        datetime_creation=str(
            datetime.strptime(
                metadata["creationTimestamp"], "%Y-%m-%dT%H:%M:%SZ"
            )
        ),
        model_id=metadata["generation"],
        model_name=metadata["name"],
        status=model["status"]["conditions"][0]["status"],
        message=model["status"]["conditions"][0].get("message", None),
        reason=model["status"]["conditions"][0].get("reason", None),
        namespace=metadata["namespace"],
        resourceVersion=metadata["resourceVersion"],
        uuid=metadata["uid"],
        image=container_data["image"],
        container_name=container_data["name"],
        ports=list(container_data["ports"]),
        url=model["status"]["url"],
    )


@router.get(
    "/pods/{model_name}",
    status_code=200,
    responses={
        200: {
            "model": List[schemas.DeployedModelPod],
            "description": "Pods of the model",
        },
        400: {
            "model": schemas.WrongResponse,
            "description": "Pod initializing",
        },
        404: {
            "model": schemas.WrongResponse,
            "description": "Model was not found",
        },
    },
)
def get_deployed_model_pods(model_name: str) -> Any:
    try:
        config.load_incluster_config()
    except config.ConfigException as cfg_ex:  # noqa F841
        config.load_kube_config()
    api = client.CustomObjectsApi()
    try:
        api.get_namespaced_custom_object(
            group="serving.knative.dev",
            version="v1",
            plural="services",
            namespace=MODELS_NAMESPACE,
            name=model_name,
        )
        pods = utils.get_pods(model_name)
    except ApiException as api_ex:
        if api_ex.status == 400:
            LOGGER.error("%s", api_ex)
            raise HTTPException(status_code=400, detail=f"{api_ex.body}")
        if api_ex.status == 404:
            LOGGER.error("%s model doesn't exist", model_name)
            raise HTTPException(status_code=404, detail="Not existing model")
        raise
    return pods
