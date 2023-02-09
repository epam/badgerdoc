from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel


class Size(BaseModel):
    width: float
    height: float


class AnnotationToken(BaseModel):
    id: int
    text: str
    x: float
    y: float
    width: float
    height: float


class AnnotationTokens(BaseModel):
    tokens: List[AnnotationToken] = []
    dataAttributes: List = []


class AnnotationLink(BaseModel):
    category_id: str = "Link"
    to: int
    type: str = "directional"
    page_num: int = 1


class Obj(BaseModel):
    id: int
    type: str
    bbox: List[float]
    category: str
    data: Optional[AnnotationTokens]
    text: str
    links: List[AnnotationLink] = []


class Page(BaseModel):
    size: Size
    page_num: int
    objs: List[Obj] = []


class BadgerdocAnnotation(BaseModel):
    size: Size
    page_num: int
    objs: List[Obj] = []


class DocumentLink(BaseModel):
    to: int
    category: str
    type: str

