from typing import List, Optional

from pydantic import field_validator, ConfigDict, BaseModel, Field

from taxonomy.errors import CheckFieldError


class TaxonBaseSchema(BaseModel):
    name: str = Field(..., examples=["taxon_name"])
    taxonomy_id: str = Field(..., examples=["my_taxonomy_id"])
    parent_id: Optional[str] = Field(None, examples=["null"])
    taxonomy_version: Optional[int] = Field(None, examples=[1])

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value or value == "null":
            raise CheckFieldError("Taxon name can not be empty.")
        return value


class TaxonInputSchema(TaxonBaseSchema):
    id: Optional[str] = Field(
        None,
        examples=["my_taxon_id"],
        description="If id is not provided, generates it as a UUID.",
    )

    @field_validator("id")
    @classmethod
    def alphanumeric_validator(cls, value):
        if value and not value.replace("_", "").isalnum():
            raise CheckFieldError("Taxon id must be alphanumeric.")
        return value


class TaxonResponseSchema(TaxonInputSchema):
    parents: List[dict] = Field(default=[])
    is_leaf: Optional[bool] = Field(default=None)
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ParentsConcatenateResponseSchema(BaseModel):
    taxon_id: str = Field(..., examples=["my_taxon_id"])
    taxon_name: str = Field(..., examples=["taxon_name"])
    parent_ids_concat: Optional[str] = Field(
        ..., examples=["parent_id_1.parent_id_2"]
    )
    parent_names_concat: Optional[str] = Field(
        ..., examples=["parent_name_1.parent_name_2"]
    )
