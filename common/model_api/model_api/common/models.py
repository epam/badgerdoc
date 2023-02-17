"""Pydantic models for requests, responses.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator


class Size(BaseModel):
    """Page size in pixels."""

    width: float
    height: float


class GeometryObject(BaseModel):
    """Bbox with a category."""

    idx: str = Field(alias="id")
    typex: Optional[str] = Field(alias="type")
    bbox: Tuple[float, float, float, float]
    category: str
    data: Optional[Dict[str, Any]]


class PageDOD(BaseModel):
    """Page with bboxes-objects."""

    page_num: int
    size: Size
    objs: List[GeometryObject]


class AnnotationFromS3(BaseModel):
    """DOD output format for s3-storage."""

    pages: List[PageDOD]


class Args(BaseModel):
    """Additional arguments for a request."""

    categories: Optional[List[str]]


# pylint: disable=E0213
class ClassifierRequest(BaseModel):
    """Request to classify DOD's bboxes."""

    input_path: Path = Field(
        example=Path("ternary_out/molecule_annotation.json")
    )
    input_field: Dict[str, Dict[str, List[str]]] = Field(
        alias="input",
        example={
            "0": {
                "1": ["30e4d539-8e90-49c7-b49c-883073e2b8c8"],
            },
            "3": {
                "1": ["aab83828-cd8b-41f7-a3c3-943f13e67c2c"],
                "2": [
                    "44d94e31-7079-470a-b8b5-74ce365353f7",
                    "d86d467f-6ec1-404e-b4e6-ba8d78f93754",
                ],
            },
        },
    )
    file: Path = Field(example=Path("molecule.pdf"))
    bucket: str = Field(example="annotation")
    pages: Optional[List[int]]
    output_path: Optional[Path] = Field(
        example=Path("ternary_out/molecule_annotation_out.json")
    )
    output_bucket: Optional[str] = Field(example="annotation")
    args: Optional[Args] = Field(example=Args(categories=["1", "3"]))

    @validator("output_bucket")
    def validate_output_path(cls, v: str, values: Dict[str, str]) -> str:
        if v is not None:
            if values["output_path"] is None:
                raise ValueError(
                    "If you define output bucket you should also define output path."
                )
        return v


class ClassifierResponse(BaseModel):
    """A service class for working with a list of pydantic models."""

    __root__: Dict[str, Dict[str, List[str]]] = Field(
        example={
            "0": {"1": ["30e4d539-8e90-49c7-b49c-883073e2b8c8"]},
            "molecule": {"1": ["aab83828-cd8b-41f7-a3c3-943f13e67c2c"]},
            "chart": {"2": ["44d94e31-7079-470a-b8b5-74ce365353f7"]},
            "not_chart": {"2": ["d86d467f-6ec1-404e-b4e6-ba8d78f93754"]},
        }
    )
