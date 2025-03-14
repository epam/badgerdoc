from enum import Enum
from typing import Optional, Union

from pydantic import AnyUrl, BaseModel


class ModelParam(BaseModel):
    param_name: str
    param_type: str
    required: bool


class ModelInfo(BaseModel):
    model_name: str
    model_params: list[ModelParam]


class UrlAsset(BaseModel):
    url: AnyUrl  # URL to the file to download


class BadgerDocAsset(BaseModel):
    asset_id: int  # ID of the asset in badgerdoc database


class InferenceInput(BaseModel):
    model_name: str
    model_params: dict
    # assets: list[Union[UrlAsset, BadgerDocAsset]]
    assets: list[Union[UrlAsset, BadgerDocAsset]]
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


class UploadResponse(BaseModel):
    asset_ids: list[int]


class InferenceStatusResponse(BaseModel):
    status: str
    data: dict[str, AnyUrl]
