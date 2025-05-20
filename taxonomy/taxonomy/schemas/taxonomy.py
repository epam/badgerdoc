from typing import Optional

from pydantic import ConfigDict, BaseModel, Field


class TaxonomyBaseSchema(BaseModel):
    name: str = Field(..., examples=["taxonomy_name"])


class TaxonomyInputSchema(TaxonomyBaseSchema):
    id: Optional[str] = Field(
        None,
        examples=["my_taxonomy_id"],
        description="If id is not provided, generates it as a UUID.",
    )


class TaxonomyResponseSchema(TaxonomyInputSchema):
    version: int = Field(description="Version of taxonomy", examples=[1])
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class CategoryLinkSchema(BaseModel):
    category_id: str = Field(
        ..., examples=["123abc"], description="Category id to link taxonomy to"
    )
    job_id: str = Field(
        ..., examples=["123abc"], description="Job id to link taxonomy to"
    )
    taxonomy_id: str = Field(..., examples=["my_taxonomy_id"])
    taxonomy_version: Optional[int] = Field(
        None, description="Version of taxonomy", examples=[1]
    )


class JobTaxonomySchema(BaseModel):
    name: str = Field(
        ..., examples=["taxonomy_name"], description="Taxonomy name"
    )
    id: str = Field(
        ..., examples=["my_taxonomy_id"], description="Taxonomy id"
    )
    version: int = Field(..., examples=[1], description="Version of taxonomy")
    category_id: str = Field(
        ..., examples=["123abc"], description="Category id to link taxonomy to"
    )
