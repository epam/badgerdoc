from typing import List

from pydantic import BaseModel, Field


class Offset(BaseModel):
    begin: int
    end: int


class BadgerdocToken(BaseModel):
    type_: str = Field(default="text", alias="type")
    bbox: List[float]
    text: str
    offset: Offset


class PageSize(BaseModel):
    width: float = Field(..., example=200.0)
    height: float = Field(..., example=300.0)


class Page(BaseModel):

    """A model for the field with bboxes."""

    page_num: int = Field(..., example=1)
    size: PageSize
    objs: List[BadgerdocToken]


class Pages(BaseModel):
    pages: List[Page]
