from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from annotation.errors import CheckFieldError


class CategoryTypeSchema(str, Enum):
    box = "box"
    link = "link"
    segmentation = "segmentation"
    document = "document"
    document_link = "document_link"


class CategoryDataAttributeNames(str, Enum):
    taxonomy_id: str = "taxonomy_id"
    taxonomy_version: Optional[str] = "taxonomy_version"

    @classmethod
    def validate_schema(cls, schema: dict) -> bool:
        if not schema:
            return False

        for attr in schema:
            if attr not in cls.__members__.keys():
                return False

        if not schema.get("taxonomy_id"):
            return False
        return True


class CategoryBaseSchema(BaseModel):
    name: str = Field(..., examples=["Title"])
    parent: Optional[str] = Field(None, examples=["null"])
    metadata: Optional[dict] = Field(None, examples=[{"color": "blue"}])
    type: CategoryTypeSchema = Field(..., examples=[CategoryTypeSchema.box])
    editor: Optional[str] = Field(None, examples=["http://editor/"])
    data_attributes: Optional[List[dict]] = Field(
        None, examples=[[{"attr_1": "value_1"}, {"attr_2": "value_2"}]]
    )


class CategoryInputSchema(CategoryBaseSchema):
    id: Optional[str] = Field(
        None,
        examples=["my_category"],
        description="If id is not provided, generates it as a UUID.",
    )

    @field_validator("id")
    @classmethod
    def alphanumeric_validator(cls, value):
        if value and not value.replace("_", "").isalnum():
            raise CheckFieldError("Category id must be alphanumeric.")
        return value


class SubCategoriesOutSchema(BaseModel):
    id: str = Field(..., examples=["123"])


class CategoryORMSchema(CategoryInputSchema):
    metadata: Optional[dict] = Field(
        None, examples=[{"color": "blue"}], alias="metadata_"
    )
    model_config = ConfigDict(from_attributes=True)


class CategoryResponseSchema(CategoryInputSchema):
    parents: Optional[List[dict]] = Field(None)
    is_leaf: Optional[bool] = Field(None)
    model_config = ConfigDict(populate_by_name=True)
