from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel

from .common import S3Path
from src.labelstudio_to_badgerdoc.labelstudio_format.labelstudio_models import ValidationType


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


