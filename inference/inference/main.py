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
    Request,
    UploadFile,
    status,
)
from tenant_dependency import TenantData, get_tenant_info

from inference.airflow_utils import get_dags
from inference.config import (
    ANNOTATION_SERVICE_HOST,
    ASSETS_SERVICE_HOST,
    BADGERDOC_EXTERNAL_PORT,
    JOBS_SERVICE_HOST,
    KEYCLOAK_HOST,
    ROOT_PATH,
    get_version,
)
from inference.models import (
    BadgerDocAsset,
    InferenceInput,
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


async def validate_model_params(inference_input: InferenceInput):
    """Check correctness of model parameters in incomming request

    Args:
        inference_input (InferenceInput): Incomming request with
            model parameters
    """
    available_models = await models()
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
    """Searches for existing categories in annotation service and adding
         categories that doesn't exist there

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
            # TODO make sure that's a proper category type
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
    logger.debug("Processing URL asset: %s", asset.url)
    # Process URL asset
    asset_url = str(asset.url)
    file_name = asset_url.split("/")[-1]
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
        logger.debug("Asset with name '%s' found in BadgerDoc", file_name)
        return asset["id"]

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
                if response_json:
                    asset_id = response_json[0]["id"]
    return asset_id


# TODO make databricks integration check jobs?/annotations? how it's done there
@app.get("/models")
async def models() -> list[ModelInfo]:
    """Get list of available ML models with their parameters"""
    dags = await get_dags()
    logger.debug(dags)
    models_list = []
    # TODO thing if we need mapping of 'dag' -> 'model'
    for dag in dags.get("dags", []):
        dag_id = dag.get("dag_id", "Unknown DAG ID")
        params = [
            ModelParam(param_name="param1", param_type="int", required=True),
            ModelParam(param_name="param2", param_type="str", required=False),
        ]
        model = ModelInfo(model_name=dag_id, model_params=params)
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
    headers = {
        "X-Current-Tenant": x_current_tenant,
        "Authorization": f"Bearer {token_data.token}",
    }

    try:
        await validate_model_params(inference_params)
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
        status=job_status, job_id=job_id, message="Inference job started"
    )


@app.get("/result/{job_id}")
async def get_inference_result(
    job_id: int,
    request: Request,
    x_current_tenant: Optional[str] = Header(None, alias="X-Current-Tenant"),
    token_data: TenantData = Depends(TENANT),
) -> InferenceStatusResponse:
    logger.debug("incomming request url: %s", request.url)
    headers = {
        "X-Current-Tenant": x_current_tenant,
        "Authorization": f"Bearer {token_data.token}",
    }
    data = {}
    async with aiohttp.request(
        "GET",
        url=f"{JOBS_SERVICE_HOST}/jobs/{job_id}",
        headers=headers,
        raise_for_status=True,
    ) as resp:
        # TODO now there is no easy way to get external Badgerdock port to
        # create redicretinon link.
        # As of now it's set by environment variable in compose.
        json_resp = await resp.json()
        status = json_resp["status"]

        for file_data in json_resp["all_files_data"]:
            file_id = file_data["id"]
            file_name = file_data["original_name"]
            scheme = request.base_url.scheme
            hostname = request.base_url.hostname
            base_url = f"{scheme}://{hostname}:{BADGERDOC_EXTERNAL_PORT}"
            file_result_link = (
                f"{base_url}/documents/{file_id}?job_id={job_id}"
            )
            data[file_name] = file_result_link

    return InferenceStatusResponse(status=status, data=data)


# TODO decide how to generate inference names
def _generate_inference_name(*args):
    return "inference_name_PLACEHOLDER_" + "_".join(args)


# TODO get pipeline name from model_name
def _get_pipeline_name(model_name: str):
    return "print"
