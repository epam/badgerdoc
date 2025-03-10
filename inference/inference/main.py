import logging
import aiohttp
import datetime
from enum import Enum
from airflow.dags.annotation.constants import ANNOTATION_HOST
from fastapi import FastAPI, HTTPException, UploadFile, UploadFile, File, Header, status
from httpx import HTTPError
from pydantic import BaseModel, AnyUrl
from typing import List, Literal, Union, Optional
from tempfile import TemporaryFile

from fastapi import Depends

from tenant_dependency import get_tenant_info, TenantData
from config import KEYCLOAK_HOST, ROOT_PATH, get_version, ASSETS_SERVICE_HOST, JOBS_SERVICE_HOST

TENANT = get_tenant_info(url=KEYCLOAK_HOST, algorithm="RS256")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Service to run inference using other BadgerDoc miscroservices",
    version=get_version(),
    root_path=ROOT_PATH,
    dependencies=[Depends(TENANT)])


class BaseInferenceError(RuntimeError):
    pass

class UnknownModelError(BaseInferenceError):
    pass

class IncorrectParam(BaseInferenceError):
    pass

class ModelParam(BaseModel):
    param_name: str
    param_type: type
    required: bool

class ModelInfo(BaseModel):
    model_name: str
    model_params: list[ModelParam]

class UrlAsset(BaseModel):
    url: AnyUrl     # URL to the file to download

class BadgerDocAsset(BaseModel):
    asset_id: int   # ID of the asset in badgerdoc database

class InferenceInput(BaseModel):
    model_name: str
    model_params: dict
    asset: Union[UrlAsset, BadgerDocAsset]
    categories: list[str]


class InferenceStatus(str, Enum):
    """Status of inference, subset of Job's statuses"""
    pending = "Pending"
    in_progress = "In Progress"
    failed = "Failed"
    finished = "Finished"

class StartInferenceResponse(BaseModel):
    status: InferenceStatus
    job_id: Union[int, None]
    message: Optional[str] = ""


async def validate_model_params(inference_input: InferenceInput):
    """Check correctness of model parameters in incomming request

    Args:
        inference_input (InferenceInput): Incomming request with model parameters
    """
    available_models = await models()
    model_params = None
    input_params = inference_input.model_params
    for model in available_models:
        if inference_input.model_name == model.model_name:
            model_params = model.model_params
    
    if model_params is None:
        raise UnknownModelError(f"Model '{inference_input.model_name}' is not supported")
    
    for model_parameter in model_params:
        # Check if required parameter is in place
        if model_parameter.param_name not in input_params:
            if model_parameter.required:
                raise IncorrectParam(f"Required parameter '{model_parameter.param_name}' is missing in request")
            else:
                logger.debug(f"Optional parameter '{model_parameter.param_name}' is not in request")
                continue

        # Check type of the input parameter
        input_param_value = input_params[model_parameter.param_name]
        if not isinstance(input_param_value, model_parameter.param_type):
            raise IncorrectParam(f"Parameter '{model_parameter.param_name}' has incorrect type:\
                                    {type(input_param_value)} Required type: {model_parameter.param_type}")


@app.get("/inference/models")
async def models() -> list[ModelInfo]:
    """Get list of available ML models with their parameters"""
    #TODO extract list of models from airflow?
    ...

    return []


async def get_asset_by_field(field_name: str, field_value: str, tenant: str, jw_token: str) -> Union[dict, None]:
    """Get asset from 'assets' service by specified field and value"""
    asset = None
    try:
        params = {
            "filters": [{"field": field_name, "operator": "eq", "value": field_value}],
        }
        assets_response = {}
        async with aiohttp.request(
            method="POST", 
            url=f"{ASSETS_SERVICE_HOST}/files/search", 
            json=params, 
            headers={
                "X-Current-Tenant": tenant,
                "Authorization": f"Bearer {jw_token}",
            }, 
            # data=data,
            raise_for_status=True
        ) as resp:
            if resp.status != status.HTTP_204_NO_CONTENT:
                assets_response = await resp.json()
                if not (not assets_response or
                    "data" not in assets_response
                    or not assets_response["data"]
                    or "id" not in assets_response["data"][0]
                ):
                    # we have given file in DB, set asset_id
                    asset = assets_response["data"][0]
            else:
                logger.warning("Received wrong response from 'assets' service: %s", assets_response)
                assets_response = None
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File wasn't found by asset service"
                )
        return asset

    except (aiohttp.client_exceptions.ClientError, HTTPException) as err:
        logger.info("Failed request to the Dataset Manager with error: %s", err)


#TODO potentially categories list can be extended to have hierarchical categories
async def get_or_set_categories(categories: list[str], tenant: str, jw_token: str) -> list[str]:
    """Searches for existing categories in annotation service and adding categories that doesn't exist there

    Args:
        categories (list[str]): list of categories to get/create
        tenant (str): current tenant
        jw_token (str): security token to send request to other services

    Returns:
        list[str]: list of categories that now exist in annotation service
    """
    search_params = {
        "filters": [{"field": "name", "operator": "in", "value": categories}],
    }
    categories_resp = []
    try:
        async with aiohttp.request(
            method="POST", 
            url=f"{ANNOTATION_HOST}/categories/search", 
            json=search_params, 
            headers={
                "X-Current-Tenant": tenant,
                "Authorization": f"Bearer {jw_token}",
            }, 
            raise_for_status=True
        ) as resp:
            categories_resp = await resp.json()
            categories_resp = categories_resp.get("data", [])
    except aiohttp.ClientError as err:
        logger.exception("Error while searching for categories: %s", categories)
        return []

    found_category_names = {cat.name for cat in categories_resp}
    missing_categories = set(categories) - found_category_names
    for missing_category in missing_categories:
         async with aiohttp.request(
            method="POST", 
            url=f"{ANNOTATION_HOST}/categories", 
            #TODO make sure that's a proper category type
            json={"name": missing_category, "type": "box"}, 
            headers={
                "X-Current-Tenant": tenant,
                "Authorization": f"Bearer {jw_token}",
            }, 
            raise_for_status=True
        ) as resp:
            #TODO don't know if we need to do anything with new categories
            category_id = (await resp.json())["id"]
    #TODO add handling exception when trying to create new categories
    return categories



@app.post("/inference/start")
async def start_inference(
    inference_params: InferenceInput, 
    file: UploadFile = File(None),
    x_current_tenant: Optional[str] = Header(
        None, alias="X-Current-Tenant"
    ),
    token_data: TenantData = Depends(TENANT)
):
    job_id = None
    asset_id = None
    try:
        await validate_model_params(inference_params)
    except BaseInferenceError as ex:
        logger.exception("Error while processing start inference request")
        raise HTTPException(status_code=400, detail="Invalid model parameters") from ex

    # Handle the `file` type separately
    if file:
        file_name = file.filename
        asset = get_asset_by_field(
            field_name="original_name", 
            field_value=file_name, 
            tenant=x_current_tenant, 
            jw_token=token_data.token
        )
        if asset:
            asset_id = asset["id"]

        # We don't have file in DB -> upload to assets what came from user
        if not asset_id:
            file_content = await file.read()
            
            # TODO Process the file (upload it to assets and don't forget to set 'asset_id' of new asset)
            ...

            asset_id = "PLACEHOLDER"
    elif isinstance(inference_params.asset, UrlAsset):
        # Process URL asset
        url = inference_params.asset.url
        try:
            file_name = url.split("/")[-1]
            asset = get_asset_by_field(
                field_name="original_name", 
                field_value=file_name, 
                tenant=x_current_tenant, 
                jw_token=token_data.token
            )
            if asset:
                asset_id = asset["id"]

            if not asset_id: 
                async with aiohttp.request(
                    method="GET", 
                    url=url, 
                    raise_for_status=True
                ) as resp:
                    response_json = await resp.read()
                    with TemporaryFile("wb") as file:
                        file.write(response_json)
                        #TODO upload downloaded file to assets and don't forget to set 'asset_id' of new asset
                        ...
                        asset_id = "PLACEHOLDER" # Will be ID of newly uploaded asset
        except aiohttp.ClientError as err:
            logger.warning("Failed download file from '%s' with error: %s", url, err)

    elif isinstance(inference_params.asset, IDAsset):
        asset = get_asset_by_field(
            field_name="id", 
            field_value=inference_params.asset.id,
            tenant=x_current_tenant,
            jw_token=token_data.token
        )
        if asset:
            asset_id = asset["id"]
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset with ID({input_data.asset.id}) not found"
            )
    
    # Find and/or create categories
    found_categories = await get_or_set_categories(
        inference_params.categories, tenant=x_current_tenant, jw_token=token_data.token)
    #TODO check if found categories are the same as categories in params. If not fail?
    ...

    # Create and start Job
    job_params = {
        "type": "ExtractionWithAnnotationJob",
        "categories": found_categories,
        "is_draft": False,
        "start_manual_job_automatically": True,
        "files": [asset_id],
        "pipeline_name": _get_pipeline_name(inference_params.model_name),
        "name": _generate_inference_name(),
        #TODO use predefined/system annotators/validators/owners
        "annotators": "annotators_PLACEHOLDER",
        "validators": "validators_PLACEHOLDER",
        "owners": "owners_PLACEHOLDER",
        #TODO check if it matters
        "deadline": datetime.datetime.now(),
        #TODO check if it's correct validation type
        "validation_type": "validation only",
    }

    request_json = {
        "job_params": job_params,
        "current_tenant": x_current_tenant,
        "token_data": token_data.token
    }
    async with aiohttp.request(
        method="POST", 
        url=f"{JOBS_SERVICE_HOST}/jobs/create_job",
        json=request_json,
        raise_for_status=True
    ) as resp:
        response_json = await resp.json()
        if response_json is None:
            logger.error("Can't create job with params: %s", request_json)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error occured when creating inference job"
            )
        logger.debug("Created inferecen job: %s", response_json)
        job_id = response_json["id"]
        #TODO create and use in response mapping of job["status"] to InferenceStatus
        job_status = response_json["status"]

    return StartInferenceResponse(
        status=job_status, 
        job_id=job_id, 
        message="Inference job started"
    )

# TODO decide how to generate inference name
def _generate_inference_name():
    return "inference_name_PLACEHOLDER"

# TODO get pipeline name from model_name
def _get_pipeline_name(model_name: str):
    return f"pipeline_for_{model_name}_PLACEHOLDER"