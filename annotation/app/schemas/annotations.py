from datetime import datetime
from typing import Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field, root_validator


class PageSchema(BaseModel):
    page_num: int = Field(..., ge=1, example=2)
    size: Dict[str, float] = Field(
        ..., example={"width": 10.2, "height": 123.34}
    )
    objs: List[dict] = Field(
        ...,
        example=[
            {
                "id": 2,
                "type": "string",
                "segmentation": {"segment": "string"},
                "bbox": [10.2, 123.34, 34.2, 43.4],
                "tokens": None,
                "links": [{"category_id": "1", "to": 2, "page_num": 2}],
                "text": "text in object",
                "category": "3",
                "data": "string",
                "children": [1, 2, 3],
            },
            {
                "id": 3,
                "type": "string",
                "segmentation": {"segment": "string"},
                "bbox": None,
                "tokens": ["token-string1", "token-string2", "token-string3"],
                "links": [{"category_id": "1", "to": 2, "page_num": 3}],
                "text": "text in object",
                "category": "3",
                "data": "string",
                "children": [1, 2, 3],
            },
        ],
    )


class PageOutSchema(PageSchema):
    revision: str = Field(
        ..., example="20fe52cce6a632c6eb09fdc5b3e1594f926eea69"
    )
    user_id: Optional[UUID] = Field(
        ..., example="c1c76433-5bfb-4c4a-a5b5-93c66fbfe376"
    )
    pipeline: Optional[int] = Field(..., example=2)
    date: datetime = Field(..., example="2021-10-19 01:01:01")
    is_validated: bool = Field(default=False, example=False)


class ParticularRevisionSchema(BaseModel):
    revision: Optional[str] = Field(
        ..., example="20fe52cce6a632c6eb09fdc5b3e1594f926eea69"
    )
    user: Optional[UUID] = Field(
        ..., example="c7311267-fdfd-4ef1-be44-160d3dd819ca"
    )
    pipeline: Optional[int] = Field(..., example=1)
    date: Optional[datetime] = Field(..., example="2021-10-19 01:01:01")
    pages: List[PageSchema]
    validated: Optional[List[int]] = Field(None, ge=1, example=[2])
    failed_validation_pages: Optional[List[int]] = Field(
        None, ge=1, example=[]
    )
    categories: Optional[List[str]] = Field(
        None, example=["science", "manifest"]
    )


class DocForSaveSchema(BaseModel):
    base_revision: Optional[str] = Field(
        None, example="20fe52cce6a632c6eb09fdc5b3e1594f926eea69"
    )
    user: Optional[UUID] = Field(
        None, example="b0ac6d8c-7b31-4570-a634-c92b07c9e566"
    )
    pipeline: Optional[int] = Field(None, example=1)
    pages: Optional[List[PageSchema]] = Field(None)
    validated: Optional[Set[int]] = Field(None, ge=1, example={1, 2, 10})
    failed_validation_pages: Optional[Set[int]] = Field(
        None, ge=1, example={3, 4}
    )
    categories: Optional[List[str]] = Field(
        None, example=["science", "manifest"]
    )

    @root_validator
    def one_field_empty_other_filled_check(cls, values):
        """
        When user_id is null, pipeline_id should not be null
        and vice versa.
        """
        user_id, pipeline_id = values.get("user"), values.get("pipeline")
        if (user_id is None and pipeline_id is None) or (
            user_id is not None and pipeline_id is not None
        ):
            raise ValueError(
                "Fields user_id and pipeline_id should "
                "not be empty or filled at the same time."
            )
        return values

    @root_validator
    def check_not_intersecting_pages(cls, values):
        """
        Same pages should not be in validated and failed
        arrays at the same time.
        """
        validated, failed = (
            values.get("validated"),
            values.get("failed_validation_pages"),
        )

        validated = set() if validated is None else validated
        failed = set() if failed is None else failed

        intersecting_pages = validated & failed
        if intersecting_pages:
            raise ValueError(
                f"Pages {intersecting_pages} "
                "should not be in validated and "
                "failed validation arrays at the "
                "same time. "
            )

        return values

    @root_validator
    def pages_for_save_check(cls, values):
        """
        Arrays pages, validated and failed
        should not be empty at the same time.
        """
        pages, validated, failed = (
            values.get("pages"),
            values.get("validated"),
            values.get("failed_validation_pages"),
        )
        if not pages and not validated and not failed:
            raise ValueError(
                "Fields pages, "
                "validated and failed validation pages are empty. "
                "Nothing to save."
            )
        return values


class AnnotatedDocSchema(BaseModel):
    revision: str = Field(
        ..., example="20fe52cce6a632c6eb09fdc5b3e1594f926eea69"
    )
    user: Optional[UUID] = Field(
        ..., example="0b0ea570-e4e8-4664-84ac-dd1122471fc5"
    )
    pipeline: Optional[int] = Field(..., example=1)
    date: datetime = Field(..., example="2021-10-19 01:01:01")
    file_id: int = Field(..., example=1)
    job_id: int = Field(..., example=1)
    pages: Dict[str, str] = Field(
        ...,
        example={
            "1": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
            "2": "adda414648714f01c1c9657646b72ebb4433c8b5",
        },
    )
    validated: Set[int] = Field(..., ge=1, example={1, 2, 10})
    failed_validation_pages: Set[int] = Field(..., ge=1, example={3, 4})
    tenant: str = Field(..., example="badger-doc")
    task_id: int = Field(None, example=2)

    class Config:
        orm_mode = True
