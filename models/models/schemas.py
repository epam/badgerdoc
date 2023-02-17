import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from models.db import StatusEnum
from pydantic import BaseModel, ConstrainedStr, Field, PositiveInt, validator


class AtLeastOneChar(ConstrainedStr):
    min_length = 1


class MinioPath(BaseModel):
    file: str = Field(
        title="Path inside the bucket",
        description="Path inside the bucket to model's config or checkpoint",
        example="custom/1.1/config.py",
    )
    bucket: str = Field(
        title="Name of the bucket",
        description="Name of bucket where model's config/checkpoint is stored",
        example="models",
    )

    # pylint: disable=no-self-argument
    @validator("bucket")
    def bucket_cannot_contain_underscore(cls, value: str) -> str:
        if "_" in value:
            raise ValueError("Bucket cannot contain underscores")
        return value


class ModelBase(BaseModel):
    name: str = Field(
        title="Description of model name",
        example="custom model based on pytorch",
    )
    basement: str = Field(
        title="Docker image's name",
        description="Name of the docker image with model logic - foreign key",
        example="custom:v1.1",
    )
    data_path: Optional[MinioPath] = Field(
        title="Checkpoint path",
        description="Json with the path to the model's checkpoint",
    )
    configuration_path: Optional[MinioPath] = Field(
        title="Config path",
        description="Json with the path to the model's config",
    )
    training_id: Optional[PositiveInt] = Field(
        title="Training id",
        description="Id of the training for that model. It's a foreign key",
        example=3,
    )
    score: Optional[float] = Field(
        description="Score of the model if it has one", example=0.89
    )
    categories: List[str] = Field(
        description="Names of supported categories", example=["string"]
    )
    type: Optional[str] = Field(
        description="Type of the model", example="preprocessing"
    )
    description: Optional[str] = Field(
        description="Description of the model", example="New model"
    )


class ModelId(BaseModel):
    id: str = Field(
        title="Model id",
        description="Model id which is the name of the model",
        example="custom",
    )


class ModelWithId(ModelBase):
    id: AtLeastOneChar = Field(
        title="Model's name",
        description=(
            "Model can be deploy and be accessible with this name. Should be "
            "unique, not longer than 15 symbol and not shorter than 1 symbol. "
            "Consist of latin lowercase letters, numbers and - only."
        ),
        example="custom",
    )

    # pylint: disable=no-self-argument
    @validator("id")
    def is_valid_resource_name(cls, value: str) -> str:
        pattern = r"^[a-z0-9][a-z0-9-]{0,14}$"
        if not re.search(pattern, value):
            raise ValueError(
                "Incorrect resource name. Use at most 15 ascii lowercase "
                "letters, - and numbers, start it with letter or number."
            )
        return value


class Model(ModelWithId):
    status: StatusEnum = Field(
        title="Status",
        description="Show if this model is available to be deployed or "
        "it has been deployed already",
        example="ready",
    )
    created_by: str = Field(description="Author who has created model", example="901")
    created_at: datetime = Field(example="2021-11-09T17:09:43.101004")
    tenant: str = Field(description="Author's tenant", example="tenant1")
    latest: bool = Field(
        description="Flag to show if version of model is latest", example=True
    )
    version: int = Field(description="Version of model", example=1)

    class Config:
        orm_mode = True


class BasementLimits(BaseModel):
    pod_cpu: str = Field("1000m", example="1000m")
    pod_memory: str = Field("4Gi", example="4Gi")
    concurrency_limit: int = Field(1, gt=0, example=1)


class BasementBase(BaseModel):
    id: AtLeastOneChar = Field(
        title="Docker image's name",
        description="Unique name of docker image to build and run",
        example="custom:v1.1",
    )
    name: str = Field(title="Human readable name", example="some describing name")
    supported_args: Optional[List[Dict[str, Any]]] = Field(
        example=[
            {
                "name": "categories",
                "type": "string",
                "multiple": True,
                "required": False,
            }
        ]
    )
    limits: BasementLimits
    gpu_support: bool = Field(title="Is gpu supported", example=False)


class BasementDelete(BaseModel):
    id: str = Field(
        title="Image's name",
        description="Unique name of the docker image to be deleted/deployed",
        example="custom:v1.1",
    )


class Basement(BasementBase):
    created_by: str = Field(
        description="Author who has created docker image", example="901"
    )
    created_at: datetime = Field(example="2021-11-09T17:09:43.101004")
    tenant: str = Field(description="Author's tenant", example="tenant1")

    class Config:
        orm_mode = True


class TrainingBase(BaseModel):
    name: str = Field(title="Training's name", example="training name")
    jobs: List[int] = Field(example=[1, 3, 5])
    basement: str = Field(
        title="Docker image's name",
        description="Name of the docker image for training (foreign key)",
        example="custom:v1.1",
    )
    epochs_count: int = Field(title="Count of training epochs", example=13)
    kubeflow_pipeline_id: Optional[str] = Field(
        example="17208425-00e9-49a0-95e7-c99da8f3b053"
    )


class TrainingUpdate(TrainingBase):
    id: PositiveInt = Field(
        description="Integer which is training's id that should be modified",
        example=3,
    )


class TrainingDelete(BaseModel):
    id: PositiveInt = Field(
        description="Integer 'id' of training that should be deleted/deployed",
        example=2,
    )


class Training(TrainingUpdate):
    created_by: str = Field(
        description="Author who has created training", example="901"
    )
    created_at: datetime = Field(example="2021-11-09T17:09:43.101004")
    tenant: str = Field(description="Author's tenant", example="tenant1")
    key_archive: str = Field(None, example="trainings/127/training_archive")
    key_annotation_dataset: str = Field(
        None, example="coco/dfedf2ed-1f11-4e44-bdbd-7c6c25111abc.zip"
    )

    class Config:
        orm_mode = True


class MsgResponse(BaseModel):
    msg: str = Field(example="Resource was created")


class WrongResponse(BaseModel):
    detail: str = Field(example="Not existing entity")


class ConnectionErrorResponse(BaseModel):
    detail: str = Field(example="Could not connect to resource")


class UnauthorisedResponse(BaseModel):
    detail: str = Field(example="No authorization provided!")


class HeaderResponse(BaseModel):
    detail: str = Field(example="Header x-current-tenant is required")


class DeployedModelMainData(BaseModel):
    datetime_creation: str = Field(example="2021-11-09T17:09:43.101004")
    status: str = Field(description="Model status, it's running or not", example=True)
    name: str = Field(description="Name of the model", example="my_model")
    url: str = Field(description="Model url with details information")


class DeployedModelDetails(BaseModel):
    apiVersion: str = Field(
        description="Version of the Kubernetes API used to create the object"
    )
    datetime_creation: str = Field(example="2021-11-09T17:09:43.101004")
    model_id: PositiveInt = Field(
        description="Integer which is id of the model", example=1
    )
    model_name: str = Field(example="my-model")
    status: str = Field(
        description="Model status, it's running or not", example="False"
    )
    reason: Optional[str] = Field(
        description="The reason of failed status if it is false",
        example="RevisionFailed",
    )
    message: Optional[str] = Field(
        description="The error message if the status is false",
        example="Revision failed with message: Unable to fetch image",
    )
    namespace: str = Field(
        description="Name of the namespace, where the model was registered",
        example="default",
    )
    resourceVersion: str = Field(example="916741")
    uuid: str = Field(
        description="Unique model identifier",
        example="e8d6a21c-801b-4ed9-bf1b-8c3df50beb5a",
    )
    image: str = Field(
        description="Path to the docker image",
        example="localhost:5000/dod:v2.1",
    )
    container_name: str = Field(
        example="inferenceservice",
    )
    ports: List[Dict[str, Union[str, int]]] = Field(
        description="List container ports and protocols"
    )
    url: str = Field(
        description="Url of the deployed model",
        example="http://dod.dev2.example.com",
    )


class Failures(BaseModel):
    reason: Optional[str] = Field(
        description="Can point to the error",
        example="Error",
    )
    message: Optional[str] = Field(
        description="The error message, can duplicate logs",
        example="NoSuchKey: message: The specified key doesn't exist",
    )


class DeployedModelPod(BaseModel):
    name: str = Field(
        description="Name of the pod",
        example="dod-00001-deployment-7656b6dc95-hqwb5",
    )
    status: str = Field(description="status of the pod", example="Running")
    failures: List[Failures] = Field(
        description="Can contains reasons and messages of any failures"
    )
    start_time: str = Field(example="2022-01-27 14:26:25+00:00")
    logs: str = Field(
        description="Recent pods of the model with their logs",
        example="[2022-01-18 09:46:07,989] - [infer] - [INFO] - [Downloading]",
    )


class MinioHTTPMethod(str, Enum):
    get_object = "get_object"
    put_object = "put_object"


class ConvertRequestSchema(BaseModel):
    job_lst: List[int] = Field(
        ...,
        description="Array of job_ids to gather annotations.",
        example=[1, 3, 5],
    )
    export_format: str = Field(
        ..., description="Annotation data conversion format.", example="coco"
    )
    validated_only: Optional[bool] = Field(
        default=False,
        description="If true - export annotations for validated pages only.",
        example=False,
    )


class TrainingCredentials(BaseModel):
    user: str = Field(..., description="Colab username", example="root")
    password: str = Field(..., description="Colab user password", example="SECRET")
    host: str = Field(
        ..., description="Ngrok host to connect colab", example="tcp.ngrok.io"
    )
    port: int = Field(..., description="Ngrok port to connect colab", example="12345")
