from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel


class Size(BaseModel):
    width: float
    height: float


class Entity(BaseModel):
    id: str


class Data(BaseModel):
    entity: Entity


class Obj(BaseModel):
    id: int
    type: str
    bbox: List[float]
    tokens: Optional[List[int]] = None
    category: str
    data: Optional[Any]
    links: List[int] = []


class Page(BaseModel):
    size: Size
    page_num: int
    objs: List[Obj] = []


class BadgerdocAnnotation(BaseModel):
    revision: Optional[str] = None
    pages: Optional[List[Page]] = []
    validated: Optional[List] = None
    failed_validation_pages: Optional[List] = None
