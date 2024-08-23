from __future__ import annotations

from typing import Any, List, Optional, Tuple

from pydantic import BaseModel


class Size(BaseModel):
    width: float
    height: float


class Entity(BaseModel):
    id: str


class AnnotationLink(BaseModel):
    category_id: str
    to: int
    type: str = "directional"
    page_num: int = 1


class Data(BaseModel):
    entity: Entity


class Obj(BaseModel):
    id: int
    type: str
    bbox: Tuple[float, float, float, float]
    tokens: List[int] = []
    category: str
    data: Optional[Any]
    links: List[AnnotationLink] = []


class Page(BaseModel):
    size: Size
    page_num: int
    objs: List[Obj] = []


class BadgerdocAnnotation(BaseModel):
    revision: Optional[str] = None
    pages: List[Page] = []
    validated: Optional[List[int]] = None
    failed_validation_pages: Optional[List[int]] = None
