from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.errors import CheckFieldError

class CategoryTypeSchema(str, Enum):
    box = "box"
    link = "link"
    segmentation = "segmentation"


class CategoryBaseSchema(BaseModel):
    name: str = Field(..., example="Title")
    parent: Optional[str] = Field(None, example="null")
    metadata: Optional[dict] = Field(None, example={"color": "blue"})
    type: CategoryTypeSchema = Field(..., example=CategoryTypeSchema.box)
    editor: Optional[str] = Field(None, example="http://editor/")
    data_attributes: Optional[List[dict]] = Field(
        None, example=[{"attr_1": "value_1"}, {"attr_2": "value_2"}]
    )


class CategoryInputSchema(CategoryBaseSchema):
    id: Optional[str] = Field(
        None,
        example="my_category",
        description="If id is not provided, generates it as a UUID.",
    )

    @validator('id')
    def alphanumeric_validator(cls, value):
        if value and not value.replace('_', '').isalnum():
            raise CheckFieldError(f'Category id must be alphanumeric.')
        return value


class SubCategoriesOutSchema(BaseModel):
    id: str = Field(..., example="123")


class CategoryORMSchema(CategoryInputSchema):
    metadata: Optional[dict] = Field(
        None, example={"color": "blue"}, alias="metadata_"
    )

    class Config:
        orm_mode = True


class CategoryResponseSchema(CategoryInputSchema):
    parents: List[dict] = Field(default=[])
    children: List[dict] = Field(default=[])

    class Config:
        allow_population_by_field_name = True
