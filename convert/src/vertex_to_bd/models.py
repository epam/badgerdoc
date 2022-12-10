from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Offset(BaseModel):
    begin: int
    end: int


class BadgerdocToken(BaseModel):
    type_: str = Field(default="text", alias="type")
    bbox: List[float]
    text: str
    offset: Offset


class VertexAnnotationToken(BaseModel):
    id_: str = Field(alias="id")
    begin: int
    end: int
    entity_type: str
    entity_name: str
    links: List[str]


class BadgerdocAnnotationToken(BaseModel):
    id_: int = Field(alias="id")
    type_: str = Field(default="text", alias="type")
    bbox: List[float]
    tokens: List[int]
    category: str
    links: List[int]
    data: Dict[str, Any]


class PageSize(BaseModel):
    width: float = Field(..., example=200.0)
    height: float = Field(..., example=300.0)


class Page(BaseModel):
    """A model for the field with bboxes."""

    page_num: int = Field(..., example=1)
    size: PageSize
    objs: List[BadgerdocToken]


class S3Path(BaseModel):
    bucket: str
    path: str


class VertexRequest(BaseModel):
    input_annotation: S3Path
    output_pdf: Optional[S3Path]
    output_tokens: Optional[S3Path]
    output_annotation: Optional[S3Path]
