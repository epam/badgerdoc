from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .common import S3Path


class LabelStudioRequest(BaseModel):
    input_annotation: S3Path
    output_bucket: str


class BadgerdocToLabelStudioRequest(BaseModel):
    input_tokens: S3Path
    input_annotation: S3Path
    output_annotation: S3Path


class Value(BaseModel):
    start: int
    end: int
    text: str
    labels: List[str]


class ResultItem(BaseModel):
    value: Optional[Value] = None
    id: str = None
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
    id: int
    model_version: str
    created_ago: str
    result: List[ResultItem1]
    score: float
    cluster: Any
    neighbors: Any
    mislabeling: float
    created_at: str
    updated_at: str
    task: int


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
    parent_prediction: int = 10
    parent_annotation: Any = None


class Data(BaseModel):
    text: str


class ModelItem(BaseModel):
    id: int = 1
    annotations: List[Annotation]
    file_upload: str = ""
    drafts: List = []
    predictions: List[int]
    data: Data
    meta: Dict[str, Any] = {}
    created_at: str = "2022-12-13T09:57:08.451845Z"
    updated_at: str = "2022-12-13T09:57:08.451845Z"
    inner_id: int = 1
    total_annotations: int = 0
    cancelled_annotations: int = 0
    total_predictions: int = 0
    comment_count: int = 0
    unresolved_comment_count: int = 0
    last_comment_updated_at: Any = ""
    project: int = 1
    updated_by: int = 1
    comment_authors: List = []


class LabelStudioModel(BaseModel):
    __root__: List[ModelItem] = []
