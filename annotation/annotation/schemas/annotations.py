from datetime import datetime
from typing import Annotated, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PageSchema(BaseModel):
    page_num: Annotated[int, Field(ge=1, examples=[2])]
    size: Dict[str, float] = Field(
        ..., examples=[{"width": 10.2, "height": 123.34}]
    )
    objs: List[dict] = Field(
        ...,
        examples=[
            [
                {
                    "id": 2,
                    "type": "string",
                    "original_annotation_id": "int",
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
                    "tokens": [
                        "token-string1",
                        "token-string2",
                        "token-string3",
                    ],
                    "links": [{"category_id": "1", "to": 2, "page_num": 3}],
                    "text": "text in object",
                    "category": "3",
                    "data": "string",
                    "children": [1, 2, 3],
                },
            ]
        ],
    )


class PageOutSchema(PageSchema):
    revision: str = Field(
        ..., examples=["20fe52cce6a632c6eb09fdc5b3e1594f926eea69"]
    )
    user_id: Optional[UUID] = Field(
        ..., examples=["c1c76433-5bfb-4c4a-a5b5-93c66fbfe376"]
    )
    pipeline: Optional[int] = Field(..., examples=[2])
    date: datetime = Field(..., examples=["2021-10-19 01:01:01"])
    is_validated: bool = Field(default=False, examples=[False])
    categories: Optional[Set[str]] = Field(None, examples=[["1", "2"]])


class RevisionLink(BaseModel):
    revision: Optional[str] = Field(
        ..., examples=["20fe52cce6a632c6eb09fdc5b3e1594f926eea69"]
    )
    job_id: int = Field(..., examples=[1])
    file_id: int = Field(..., examples=[1])
    label: str = Field(..., examples=["similar"])


class ParticularRevisionSchema(BaseModel):
    revision: Optional[str] = Field(
        ..., examples=["20fe52cce6a632c6eb09fdc5b3e1594f926eea69"]
    )
    user: Optional[UUID] = Field(
        ..., examples=["c7311267-fdfd-4ef1-be44-160d3dd819ca"]
    )
    pipeline: Optional[int] = Field(..., examples=[1])
    date: Optional[datetime] = Field(..., examples=["2021-10-19 01:01:01"])
    pages: List[PageSchema]
    validated: Optional[List[int]] = Field(None, examples=[[2]])
    failed_validation_pages: Optional[
        Annotated[
            List[Annotated[int, Field(ge=1)]],
            Field(
                description="A list of integers where each value must be >= 1."
            ),
        ]
    ] = Field(None, examples=[[]])

    similar_revisions: Optional[List[RevisionLink]] = Field(None)
    categories: Optional[Set[str]] = Field(None, examples=[["1", "2"]])
    links_json: Optional[List[dict]] = Field(
        None,
        examples=[
            [{"to": 2, "category": "my_category", "type": "directional"}]
        ],
    )


class DocForSaveSchema(BaseModel):
    base_revision: Optional[str] = Field(
        None, examples=["20fe52cce6a632c6eb09fdc5b3e1594f926eea69"]
    )
    user: Optional[UUID] = Field(
        None, examples=["b0ac6d8c-7b31-4570-a634-c92b07c9e566"]
    )
    pipeline: Optional[int] = Field(None, examples=[1])
    pages: Optional[List[PageSchema]] = Field(None)
    validated: Optional[
        Annotated[
            Set[int],
            Field(
                description="A set of integers where each value must be >= 1"
            ),
        ]
    ] = Field(None, examples=[{1, 2, 10}])
    failed_validation_pages: Optional[
        Annotated[
            Set[int],
            Field(
                description=(
                    "A set of integers representing failed validation pages."
                )
            ),
        ]
    ] = Field(None, examples=[{3, 4}])
    similar_revisions: Optional[List[RevisionLink]] = Field(None)
    categories: Optional[Set[str]] = Field(None, examples=[["1", "2"]])
    links_json: Optional[List[dict]] = Field(
        None,
        examples=[
            [{"to": 2, "category": "my_category", "type": "directional"}]
        ],
    )

    @model_validator(mode="after")
    def one_field_empty_other_filled_check(cls, values):
        """
        When user_id is null, pipeline_id should not be null
        and vice versa.
        """
        user_id, pipeline_id = (
            getattr(values, "user", None),
            getattr(values, "pipeline", None),
        )
        if (user_id is None and pipeline_id is None) or (
            user_id is not None and pipeline_id is not None
        ):
            raise ValueError(
                "Fields user_id and pipeline_id should "
                "not be empty or filled at the same time."
            )
        return values

    @model_validator(mode="after")
    def check_not_intersecting_pages(cls, values):
        """
        Same pages should not be in annotated or failed
        arrays at the same time.
        """
        annotated, validated, failed = (
            set(i.page_num for i in (getattr(values, "pages", []) or [])),
            getattr(values, "validated", set()) or set(),
            getattr(values, "failed_validation_pages", set()) or set(),
        )

        intersecting_pages = annotated.intersection(failed)
        intersecting_pages.update(validated.intersection(failed))

        if intersecting_pages:
            raise ValueError(
                f"Pages {intersecting_pages} "
                "should not be in annotated (pages), and "
                "failed validation arrays at the "
                "same time. "
            )
        return values

    @model_validator(mode="after")
    def pages_for_save_check(cls, values):
        """
        Arrays pages, validated, failed and categories
        should not be empty at the same time.
        """
        pages, validated, failed, categories = (
            getattr(values, "pages", None),
            getattr(values, "validated", None),
            getattr(values, "failed_validation_pages", None),
            getattr(values, "categories", None),
        )

        if all(i is None for i in (pages, validated, failed, categories)):
            raise ValueError(
                "Fields pages, "
                "validated, failed validation pages "
                "and categories are empty. Nothing to save."
            )
        return values


class AnnotatedDocSchema(BaseModel):
    revision: str = Field(
        ..., examples=["20fe52cce6a632c6eb09fdc5b3e1594f926eea69"]
    )
    user: Optional[UUID] = Field(
        ..., examples=["0b0ea570-e4e8-4664-84ac-dd1122471fc5"]
    )
    pipeline: Optional[int] = Field(..., examples=[1])
    date: datetime = Field(..., examples=["2021-10-19 01:01:01"])
    file_id: int = Field(..., examples=[1])
    job_id: int = Field(..., examples=[1])
    pages: Dict[str, str] = Field(
        ...,
        examples=[
            {
                "1": "19fe52cce6a632c6eb09fdc5b3e1594f926eea69",
                "2": "adda414648714f01c1c9657646b72ebb4433c8b5",
            }
        ],
    )

    validated: Annotated[
        Set[Annotated[int, Field(ge=1)]], Field(examples=[{1, 2, 10}])
    ]

    failed_validation_pages: Annotated[
        Set[Annotated[int, Field(ge=1)]], Field(examples=[{3, 4}])
    ]
    tenant: str = Field(..., examples=["badger-doc"])
    task_id: int = Field(None, examples=[2])
    similar_revisions: Optional[List[RevisionLink]] = Field(None)
    categories: Optional[Set[str]] = Field(None, examples=[["1", "2"]])
    links_json: Optional[List[dict]] = Field(
        None,
        examples=[
            [{"to": 2, "category": "my_category", "type": "directional"}]
        ],
    )

    @classmethod
    def from_orm(cls, obj):
        value = super().from_orm(obj)
        if links := obj.links:
            value.similar_revisions = [
                RevisionLink(
                    revision=link.similar_doc.revision,
                    job_id=link.similar_doc.job_id,
                    file_id=link.similar_doc.file_id,
                    label=link.label,
                )
                for link in links
            ]
        return value

    model_config = ConfigDict(from_attributes=True)
