"""Contain model for saving page data as JSON"""
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator

BBOX = Tuple[float, float, float, float]


class Status(str, Enum):
    PEND = "Pending"
    RUN = "Running"
    DONE = "Finished"
    FAIL = "Failed"


class StatusForUpdate(str, Enum):
    RUN = "Running"
    DONE = "Finished"
    FAIL = "Failed"


class PreprocessingStatus(str, Enum):
    PREPROCESSING_IN_PROGRESS = "preprocessing in progress"
    PREPROCESSED = "preprocessed"
    FAILED = "failed"


class UpdateStatusRequest(BaseModel):
    status: StatusForUpdate


class ParagraphBbox(BaseModel):
    """Main bbox with nested bboxes."""

    bbox: List[float]
    nested_bboxes: List[Dict[str, Any]]


class MatchedPage(BaseModel):
    """A model of page with bboxes."""

    page_num: int
    paragraph_bboxes: Dict[int, ParagraphBbox]


class PageSize(BaseModel):
    width: float = Field(..., example=200.0)
    height: float = Field(..., example=300.0)


class Page(BaseModel):
    """A model for the field with bboxes."""

    page_num: int = Field(..., example=1)
    size: PageSize
    objs: List[Dict[str, Any]] = Field(
        ...,
        example=[{"id": 1, "bbox": [1, 2, 3, 4], "category": "1", "text": "string"}],
    )


class Input(BaseModel):
    pages: List[Page]


# pylint: disable=E0213
class AnnotationData(BaseModel):
    """A model for an input request."""

    file: str = Field(..., title="Path to input PDF", example="files/4/4.pdf")
    bucket: str = Field(..., title="Bucket in the MinIO", example="test")
    input: Input = Field(..., title="Pages with annotations")
    input_path: Optional[Path] = Field(
        default=None,
        title="Path to ocr JSON",
        description='Default path is a folder "ocr" nearby `file`.',
        example="ocr",
    )

    @validator("file")
    def validate_file_extension(cls, file: str) -> str:
        allowed_extension = (".pdf", ".jpg", ".jpeg")
        if os.path.splitext(file)[1] not in allowed_extension:
            raise ValueError("File extension must be pdf")
        return file

    @validator("input_path", always=True)
    def set_default_ocr(
        cls,
        input_path: Optional[Path],
        values: Dict[str, Any],
    ) -> Optional[Path]:
        # As validator's flag "always" is True it can suppress for
        # `path_extension_must_be_pdf` validator error, so check
        # that `file` validator passed successfully
        file: Path = values.get("file")  # type: ignore
        if file is None:
            return None
        file_ = Path(file)
        return input_path if input_path else file_.parent / "ocr/"


# pylint: disable=E0213
class PreprocessExecuteRequest(BaseModel):
    """Request body for `/run_preprocess endpoint`"""

    file_ids: List[int] = Field(..., example=[4, 52])
    pipeline_id: int = Field(
        ...,
        description="Id of pipeline to executing",
        example=123,
    )
    languages: Optional[List[str]] = Field(
        default=None,
        description="Languages for OCR to recognize text",
        example=["rus", "eng"],
    )


class MinioProblem(BaseModel):
    detail: str = Field(example="raw minio exception text")


class PreprocessingResultResponse(BaseModel):
    """Response with preprocessing result."""

    __root__: Dict[str, Any] = Field(
        example=[
            {
                "size": {"width": 612, "height": 792},
                "page_num": 2,
                "objs": [
                    {
                        "type": "text",
                        "bbox": [307.14, 143.27, 327.14, 153.27],
                        "text": "word",
                    }
                ],
            },
            {
                "size": {"width": 612, "height": 792},
                "page_num": 1,
                "objs": [
                    {
                        "type": "text",
                        "bbox": [370.52, 226.934, 376.08, 236.934],
                        "text": "word",
                    }
                ],
            },
        ]
    )
