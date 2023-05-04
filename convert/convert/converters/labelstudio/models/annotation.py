from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ValidationType(str, Enum):
    cross = "cross"
    hierarchical = "hierarchical"
    validation_only = "validation only"
    extensive_coverage = "extensive_coverage"


class Value(BaseModel):
    start: int
    end: int
    text: str
    labels: List[str]
    taxons: Optional[List[Any]] = None


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
    labels: Optional[List[str]] = None


class ValuePredictionItem(BaseModel):
    start: int
    end: int
    score: float
    text: str
    labels: List[str]


class ResultPredictionItem(BaseModel):
    id: str
    from_name: str
    to_name: str
    type: str
    value: ValuePredictionItem


class Prediction(BaseModel):
    id: Optional[int] = None
    model_version: Optional[str] = None
    created_ago: Optional[str] = None
    result: Optional[List[ResultPredictionItem]] = None
    score: Optional[float] = None
    cluster: Optional[Any] = None
    neighbors: Optional[Any] = None
    mislabeling: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    task: Optional[int] = None


class Annotation(BaseModel):
    id: int
    completed_by: Optional[int] = None
    result: List[ResultItem]
    was_cancelled: bool = False
    ground_truth: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    lead_time: float = 0
    prediction: Optional[Prediction] = None
    result_count: int = 0
    task: int = 1
    parent_prediction: Optional[int] = None
    parent_annotation: Optional[Any] = None


class Data(BaseModel):
    text: str


class DocumentRelation(BaseModel):
    category: str
    to: int
    type: str


class Meta(BaseModel):
    labels: List[Any] = []
    relations: List[DocumentRelation] = []
    categories_to_taxonomy_mapping: Dict[str, Dict[str, str]] = {}


class ModelItem(BaseModel):
    id: int = 1
    annotations: List[Annotation] = []
    file_upload: str = ""
    drafts: List[Annotation] = []
    predictions: List[int] = []
    data: Data
    meta: Meta = Meta()
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    inner_id: int = 1
    total_annotations: Optional[int] = None
    cancelled_annotations: Optional[int] = None
    total_predictions: int = 0
    comment_count: int = 0
    unresolved_comment_count: int = 0
    last_comment_updated_at: Optional[Any] = None
    project: int = 1
    updated_by: int = 1
    comment_authors: List[str] = []


class LabelStudioModel(BaseModel):
    __root__: List[ModelItem] = []
