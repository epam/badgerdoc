from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from src.converters.labelstudio.models.annotation import ValidationType

from .common import S3Path


class LabelStudioRequest(BaseModel):
    input_annotation: S3Path
    output_bucket: str
    validation_type: ValidationType
    deadline: Optional[datetime] = None
    extensive_coverage: Optional[int] = None
    annotators: List[str] = []
    validators: List[str] = []


class BadgerdocToLabelStudioRequest(BaseModel):
    input_tokens: S3Path
    input_annotation: S3Path
    input_manifest: S3Path
    output_annotation: S3Path
