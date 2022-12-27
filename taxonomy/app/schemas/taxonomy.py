from typing import Optional

from pydantic import BaseModel, Field


class TaxonomyBaseSchema(BaseModel):
    name: str = Field(..., example="taxonomy_name")


class TaxonomyInputSchema(TaxonomyBaseSchema):
    id: Optional[str] = Field(
        None,
        example="my_taxonomy_id",
        description="If id is not provided, generates it as a UUID.",
    )


class TaxonomyResponseSchema(TaxonomyInputSchema):
    version: int = Field(description="Version of taxonomy", example=1)

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class CategoryLinkSchema(BaseModel):
    category_id: str = Field(
        ..., example="123abc", description="Category id to link taxonomy to"
    )
    job_id: str = Field(
        ..., example="123abc", description="Job id to link taxonomy to"
    )
    taxonomy_id: str = Field(..., example="my_taxonomy_id")
    taxonomy_version: Optional[int] = Field(
        description="Version of taxonomy", example=1
    )


class JobTaxonomySchema(BaseModel):
    name: str = Field(
        ..., example="taxonomy_name", description="Taxonomy name"
    )
    id: str = Field(..., example="my_taxonomy_id", description="Taxonomy id")
    version: int = Field(..., example=1, description="Version of taxonomy")
    category_id: str = Field(
        ..., example="123abc", description="Category id to link taxonomy to"
    )
