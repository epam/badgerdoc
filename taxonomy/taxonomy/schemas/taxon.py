from typing import List, Optional

from pydantic import BaseModel, Field, validator
from taxonomy.errors import CheckFieldError


class TaxonBaseSchema(BaseModel):
    name: str = Field(..., example="taxon_name")
    taxonomy_id: str = Field(..., example="my_taxonomy_id")
    parent_id: Optional[str] = Field(None, example="null")
    taxonomy_version: Optional[int] = Field(None, example=1)

    @validator("name")
    def validate_name(cls, value):
        if not value or value == "null":
            raise CheckFieldError("Taxon name can not be empty.")
        return value


class TaxonInputSchema(TaxonBaseSchema):
    id: Optional[str] = Field(
        None,
        example="my_taxon_id",
        description="If id is not provided, generates it as a UUID.",
    )

    @validator("id")
    def alphanumeric_validator(cls, value):
        if value and not value.replace("_", "").isalnum():
            raise CheckFieldError("Taxon id must be alphanumeric.")
        return value


class TaxonResponseSchema(TaxonInputSchema):
    parents: List[dict] = Field(default=[])
    is_leaf: Optional[bool] = Field(default=None)

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class ParentsConcatenateResponseSchema(BaseModel):
    taxon_id: str = Field(..., example="my_taxon_id")
    taxon_name: str = Field(..., example="taxon_name")
    parent_ids_concat: Optional[str] = Field(..., example="parent_id_1.parent_id_2")
    parent_names_concat: Optional[str] = Field(
        ..., example="parent_name_1.parent_name_2"
    )
