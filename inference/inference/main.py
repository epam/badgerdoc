import datetime
import logging
import logging.handlers
from tempfile import TemporaryFile
from typing import Optional, Union

import aiohttp
from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    UploadFile,
    status,
)
from tenant_dependency import TenantData, get_tenant_info

from inference.config import (
    ANNOTATION_SERVICE_HOST,
    ASSETS_SERVICE_HOST,
    JOBS_SERVICE_HOST,
    KEYCLOAK_HOST,
    ROOT_PATH,
    get_version,
)
from inference.models import (
    BadgerDocAsset,
    InferenceInput,
    InferenceStatusFileData,
    InferenceStatusResponse,
    ModelInfo,
    ModelParam,
    StartInferenceResponse,
    UploadResponse,
    UrlAsset,
)

TENANT = get_tenant_info(url=KEYCLOAK_HOST, algorithm="RS256")
# TODO remove after testing
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Service to run inference using other BadgerDoc miscroservices",
    version=get_version(),
    root_path=ROOT_PATH,
    dependencies=[Depends(TENANT)],
)


class BaseInferenceError(RuntimeError):
    pass


class UnknownModelError(BaseInferenceError):
    pass


class IncorrectParam(BaseInferenceError):
    pass


async def validate_model_params(
    inference_input: InferenceInput, available_models: list[ModelInfo]
):
    """Check correctness of model parameters in incomming request

    Args:
        inference_input (InferenceInput): Incomming request with
            model parameters
        available_models (list[ModelInfo]): supported models info
    """
    model_params = None
    input_params = inference_input.model_params
    for model in available_models:
        if inference_input.model_name == model.model_name:
            model_params = model.model_params

    if model_params is None:
        raise UnknownModelError(
            f"Model '{inference_input.model_name}' is not supported"
        )

    for model_parameter in model_params:
        # Check if required parameter is in place
        if model_parameter.param_name not in input_params:
            if model_parameter.required:
                raise IncorrectParam(
                    (
                        f"Required parameter '{model_parameter.param_name}'",
                        " is missing in request",
                    )
                )
            else:
                logger.debug(
                    (
                        f"Optional parameter '{model_parameter.param_name}'"
                        " is not in request"
                    )
                )
                continue

        # Check type of the input parameter
        input_param_value = input_params[model_parameter.param_name]
        if not isinstance(input_param_value, eval(model_parameter.param_type)):
            param_name = model_parameter.param_name
            param_type = model_parameter.param_type
            raise IncorrectParam(
                (
                    f"Parameter '{param_name}' has incorrect type:",
                    f"{type(input_param_value)} Required type: {param_type}",
                )
            )


async def get_asset_by_field(
    field_name: str, field_value: str, tenant: str, jw_token: str
) -> Union[dict, None]:
    """Get asset from 'assets' service by specified field and value"""
    asset = None
    try:
        params = {
            "filters": [
                {"field": field_name, "operator": "eq", "value": field_value}
            ],
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
            raise_for_status=True,
        ) as resp:
            if resp.status != status.HTTP_204_NO_CONTENT:
                assets_response = await resp.json()
                if not (
                    not assets_response
                    or "data" not in assets_response
                    or not assets_response["data"]
                    or "id" not in assets_response["data"][0]
                ):
                    # we have given file in DB, set asset_id
                    asset = assets_response["data"][0]
            else:
                logger.warning(
                    "Received wrong response from 'assets' service: %s",
                    assets_response,
                )
                assets_response = None
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File wasn't found by asset service",
                )
        return asset

    except (aiohttp.ClientError, HTTPException):
        logger.exception("Failed request to the Dataset Manager")


# TODO potentially categories list can be extended to
# have hierarchical categories
async def get_or_set_categories(
    categories: list[str], tenant: str, jw_token: str
) -> list[str]:
    """Search for existing categories in annotation service and add
         categories that don't exist there

    Args:
        categories (list[str]): list of categories to get/create

    Returns:
        list[str]: list of category IDs that now exist in annotation service
    """
    search_params = {
        "filters": [{"field": "name", "operator": "in", "value": categories}],
    }
    categories_id = []
    async with aiohttp.request(
        method="POST",
        url=f"{ANNOTATION_SERVICE_HOST}/categories/search",
        json=search_params,
        headers={
            "X-Current-Tenant": tenant,
            "Authorization": f"Bearer {jw_token}",
        },
        raise_for_status=True,
    ) as resp:
        categories_resp = await resp.json()
        found_categories = categories_resp.get("data", [])
        logger.debug("Found next categories: %s", found_categories)
        for category in found_categories:
            categories_id.append(category["id"])

    found_category_names = {category["name"] for category in found_categories}
    missing_categories = set(categories) - found_category_names
    for missing_category in missing_categories:
        async with aiohttp.request(
            method="POST",
            url=f"{ANNOTATION_SERVICE_HOST}/categories",
            json={"name": missing_category, "type": "box"},
            headers={
                "X-Current-Tenant": tenant,
                "Authorization": f"Bearer {jw_token}",
            },
            raise_for_status=True,
        ) as resp:
            category_id = (await resp.json())["id"]
            categories_id.append(category_id)
    return categories_id


async def _process_inference_file(
    file: UploadFile, tenant: str, jw_token: str
) -> int:
    """Helper function to process uploaded files

    Process and send uploaded file to Assets service
    Args:
        file (UploadFile): file to process
        tenant (str): current tenant to send request to Assets service
        jw_token (str): token to send request to Assets service

    Returns:
        int: asset ID under which it's stored in BadgerDoc
    """
    file_name = file.filename
    headers = {
        "X-Current-Tenant": tenant,
        "Authorization": f"Bearer {jw_token}",
    }
    asset = await get_asset_by_field(
        field_name="original_name",
        field_value=file_name,
        tenant=tenant,
        jw_token=jw_token,
    )
    if asset and asset.get("id"):
        return asset["id"]

    logger.info("File '%s' not found in assets. Will upload it", file_name)

    # We don't have file in DB -> upload to assets file from user
    try:
        form_data = aiohttp.FormData()
        form_data.add_field(
            name="files",
            value=file.file,
            filename=file.filename,
            content_type=file.content_type,
        )
        async with aiohttp.request(
            method="POST",
            url=f"{ASSETS_SERVICE_HOST}/files",
            headers=headers,
            raise_for_status=True,
            data=form_data,
        ) as resp:
            response_json = await resp.json()
            asset_id = response_json.get("id")
    except aiohttp.ClientError as ex:
        logger.exception("Can't upload file to assets")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error occured when uploading file to assets",
        ) from ex

    return asset_id


async def _process_url_asset(
    asset: UrlAsset, tenant: str, jw_token: str
) -> int:
    """Helper function to process assets from urls

    Download asset from url and send request to Assets service to store it.
    Args:
        asset (UrlAsset): url asset to download
        tenant (str): current tenant to send request to Assets service
        jw_token (str): token to send request to Assets service

    Returns:
        int: asset ID under which it's stored in BadgerDoc
    """
    logger.debug("Processing URL asset: %s", asset.url)
    # Process URL asset
    asset_url = str(asset.url)
    file_name = asset_url.split("/")[-1]
    headers = {
        "X-Current-Tenant": tenant,
        "Authorization": f"Bearer {jw_token}",
    }
    # TODO responsibility of checking duplicates should be moved to assets/
    # asset = await get_asset_by_field(
    #     field_name="original_name",
    #     field_value=file_name,
    #     tenant=tenant,
    #     jw_token=jw_token,
    # )
    # if asset and asset.get("id"):
    #     logger.debug("Asset with name '%s' found in BadgerDoc", file_name)
    #     return asset["id"]

    logger.debug("Asset with name '%s' is not found in BadgerDoc", file_name)
    async with aiohttp.request(
        method="GET", url=asset_url, headers=headers, raise_for_status=True
    ) as resp:
        response_data = await resp.read()
        with TemporaryFile("bw+") as file:
            file.write(response_data)
            file.flush()
            file.seek(0)
            form_data = aiohttp.FormData()
            form_data.add_field(
                name="files",
                value=file,
                filename=file_name,
                content_type="application/octet-stream",
            )
            async with aiohttp.request(
                method="POST",
                url=f"{ASSETS_SERVICE_HOST}/files",
                headers=headers,
                raise_for_status=True,
                data=form_data,
            ) as resp:
                response_json = await resp.json()
                logger.debug("Response from assets: %s", response_json)
                if response_json:
                    asset_id = response_json[0]["id"]

    if asset_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset with url '{asset_url}' can't be processed",
        )
    return asset_id


# TODO make request to jobs/ to get pipelines info instead of going straight
# to Airflow/Databricks
@app.get("/models")
async def models(
    x_current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    token_data: TenantData = Depends(TENANT),
) -> list[ModelInfo]:
    """Get list of available ML models with their parameters"""
    headers = {
        "X-Current-Tenant": x_current_tenant,
        "Authorization": f"Bearer {token_data.token}",
    }
    models_list = []
    engines_resources = []
    # Get available pipelines engines to exctract pipelines from them after
    async with aiohttp.request(
        method="GET",
        url=f"{JOBS_SERVICE_HOST}/pipelines/support",
        headers=headers,
        raise_for_status=True,
    ) as resp:
        pipeline_engines = (await resp.json())["data"]
        logger.debug("Got next pipelines support: %s", pipeline_engines)
        for engine in pipeline_engines:
            if engine.get("enabled"):
                engines_resources.append(engine.get("resource"))

    for resource in engines_resources:
        async with aiohttp.request(
            method="GET",
            url=f"{JOBS_SERVICE_HOST}{resource}",
            headers=headers,
            raise_for_status=True,
        ) as resp:
            pipelines = (await resp.json())["data"]
            logger.debug("Got next pipelines: %s", pipelines)
            for pipeline in pipelines:
                name = pipeline.get("name")
                # TODO each model should have set of accepeted parameters
                # configured  we should think of were to keep it
                params = [
                    ModelParam(
                        param_name="param1", param_type="int", required=True
                    ),
                    ModelParam(
                        param_name="param2", param_type="str", required=False
                    ),
                ]
                model = ModelInfo(model_name=name, model_params=params)
                models_list.append(model)

    return models_list


@app.post("/upload_files")
async def upload_files(
    files: list[UploadFile] = File(default=None),
    x_current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    token_data: TenantData = Depends(TENANT),
) -> UploadResponse:
    """Upload files to badgerdoc

    Args:
        files (list[UploadFile], optional): List of files data to upload.
            Defaults to File(default=None).

    Returns:
        UploadResponse: Response with list of asset IDs of uploaded files
    """
    asset_ids = []
    for file in files:
        asset_id = await _process_inference_file(
            file, x_current_tenant, token_data.token
        )
        asset_ids.append(asset_id)

    return UploadResponse(asset_ids=asset_ids)


@app.post("/start")
async def start_inference(
    inference_params: InferenceInput,
    x_current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    token_data: TenantData = Depends(TENANT),
) -> StartInferenceResponse:
    job_id = None
    asset_ids = []
    files_data = dict()
    headers = {
        "X-Current-Tenant": x_current_tenant,
        "Authorization": f"Bearer {token_data.token}",
    }

    try:
        available_models = await models(
            x_current_tenant=x_current_tenant, token_data=token_data
        )
        await validate_model_params(inference_params, available_models)
    except BaseInferenceError as ex:
        logger.exception("Error while processing start inference request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model parameters",
        ) from ex

    if not inference_params.assets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No assets in request",
        )
    elif isinstance(inference_params.assets[0], UrlAsset):
        try:
            for asset in inference_params.assets:
                asset_id = await _process_url_asset(
                    asset, x_current_tenant, token_data.token
                )
                files_data[asset.url] = asset_id
                asset_ids.append(asset_id)
        except (aiohttp.ClientError, HTTPException) as err:
            logger.exception("Failed file download from '%s'", asset.url)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to download one or more files",
            ) from err
    elif isinstance(inference_params.assets[0], BadgerDocAsset):
        for asset in inference_params.assets:
            bd_asset = await get_asset_by_field(
                field_name="id",
                field_value=asset.asset_id,
                tenant=x_current_tenant,
                jw_token=token_data.token,
            )
            if bd_asset and "id" in bd_asset:
                files_data[asset.asset_id] = bd_asset["id"]
                asset_ids.append(bd_asset["id"])
            else:
                asset_id = asset.asset_id
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Asset ID({asset_id}) not found in BadgerDoc",
                )

    # Find and/or create categories
    found_categories_id = await get_or_set_categories(
        inference_params.categories,
        tenant=x_current_tenant,
        jw_token=token_data.token,
    )

    # Create and start Job
    job_params = {
        "name": _generate_inference_name(
            inference_params.model_name,
            str(datetime.datetime.now().timestamp()),
        ),
        "type": "ExtractionJob",
        "files": asset_ids,
        "revisions": [],
        "is_draft": False,
        # ExtractionJob params
        "pipeline_name": _get_pipeline_name(inference_params.model_name),
        "pipeline_id": _get_pipeline_name(inference_params.model_name),
        # TODO select based on model type?
        "pipeline_engine": "airflow",
        "categories": found_categories_id,
    }

    logger.debug("Sending request to jobs/ with params:\n%s", job_params)
    async with aiohttp.request(
        method="POST",
        url=f"{JOBS_SERVICE_HOST}/jobs/create_job",
        headers=headers,
        json=job_params,
        raise_for_status=True,
    ) as resp:
        response_json = await resp.json()
    if response_json is None:
        logger.error("Can't create job with params: %s", job_params)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error occured when creating inference job",
        )
    logger.debug("Created inferecen job: %s", response_json)
    job_id = response_json["id"]
    # TODO use in response mapping of job["status"] to InferenceStatus
    job_status = response_json["status"]

    return StartInferenceResponse(
        status=job_status,
        job_id=job_id,
        files_data=files_data,
        message="Inference job started",
    )


@app.get("/result/{job_id}")
async def get_inference_result(
    job_id: int,
    x_current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    token_data: TenantData = Depends(TENANT),
) -> InferenceStatusResponse:
    headers = {
        "X-Current-Tenant": x_current_tenant,
        "Authorization": f"Bearer {token_data.token}",
    }
    files_data = []
    async with aiohttp.request(
        "GET",
        url=f"{JOBS_SERVICE_HOST}/jobs/{job_id}",
        headers=headers,
        raise_for_status=True,
    ) as resp:
        json_resp = await resp.json()
        status = json_resp["status"]

        # TODO add files_data only if job is finished
        for file_data in json_resp["all_files_data"]:
            file_id = file_data["id"]
            file_name = file_data["original_name"]
            annotation_url = (
                "annotation/annotation/" f"{job_id}/{file_id}/latest"
            )
            files_data.append(
                InferenceStatusFileData(
                    file_id=file_id,
                    filename=file_name,
                    annotation_url=annotation_url,
                )
            )

    return InferenceStatusResponse(status=status, files_data=files_data)


# TODO decide how to generate inference names
def _generate_inference_name(*args):
    return "inference_name_PLACEHOLDER_" + "_".join(args)


# TODO get pipeline name from model_name
def _get_pipeline_name(model_name: str):
    return "print"
