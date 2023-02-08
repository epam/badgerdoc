from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel

from .common import S3Path


class ValidationType(str, Enum):
    cross = "cross"
    hierarchical = "hierarchical"
    validation_only = "validation only"
    extensive_coverage = "extensive_coverage"


class LabelStudioRequest(BaseModel):
    input_annotation: S3Path
    output_bucket: str
    validation_type: ValidationType
    deadline: Optional[datetime]
    extensive_coverage: Optional[int] = None
    annotators: List[str] = []
    validators: List[str] = []


class BadgerdocToLabelStudioRequest(BaseModel):
    input_tokens: S3Path
    input_annotation: S3Path
    input_manifest: S3Path
    output_annotation: S3Path


class Value(BaseModel):
    start: int
    end: int
    text: str
    labels: List[str]
    taxons: Optional[List[Any]]


class ResultItem(BaseModel):
    value: Optional[Value] = None
    id: Optional[str] = None
    from_name: Optional[str] = None
    to_name: Optional[str] = None
    type: str
    origin: Optional[str] = None
    from_id: Optional[str] = None
    to_id: Optional[str] = None
    direction: Optional[str] = None
    labels: Optional[List] = None


class Value1(BaseModel):
    start: int
    end: int
    score: float
    text: str
    labels: List[str]


class ResultItem1(BaseModel):
    id: str
    from_name: str
    to_name: str
    type: str
    value: Value1


class Prediction(BaseModel):
    id: Optional[int]
    model_version: Optional[str]
    created_ago: Optional[str]
    result: Optional[List[ResultItem1]]
    score: Optional[float]
    cluster: Optional[Any]
    neighbors: Optional[Any]
    mislabeling: Optional[float]
    created_at: Optional[str]
    updated_at: Optional[str]
    task: Optional[int]


class Annotation(BaseModel):
    id: int = 7
    completed_by: int = 1
    result: List[ResultItem]
    was_cancelled: bool = False
    ground_truth: bool = False
    created_at: str = "2022-12-13T09:57:08.451845Z"
    updated_at: str = "2022-12-13T09:57:08.451875Z"
    lead_time: float = 121.434
    prediction: Optional[Prediction] = None
    result_count: int = 0
    task: int = 3
    parent_prediction: Optional[int] = 10
    parent_annotation: Optional[Any] = None


class Data(BaseModel):
    text: str


class DocumentRelation(BaseModel):
    category: str
    to: str
    type: str
    

class Meta(BaseModel):
    labels: List[Any] = []
    relations: List[DocumentRelation] = []
    categories_to_taxonomy_mapping = {}

class ModelItem(BaseModel):
    id: int = 1
    annotations: List[Annotation]
    file_upload: str = ""
    drafts: List = []
    predictions: List[int] = []
    data: Data
    meta: Meta = Meta(labels=[], relations=[])
    created_at: Optional[str] = "2022-12-13T09:57:08.451845Z"
    updated_at: Optional[str] = "2022-12-13T09:57:08.451845Z"
    inner_id: int = 1
    total_annotations: int = 0
    cancelled_annotations: int = 0
    total_predictions: int = 0
    comment_count: int = 0
    unresolved_comment_count: int = 0
    last_comment_updated_at: Optional[Any] = None
    project: int = 1
    updated_by: int = 1
    comment_authors: List[str] = []


class LabelStudioModel(BaseModel):
    __root__: List[ModelItem] = []
