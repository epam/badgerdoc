from typing import Optional, List

from pydantic import BaseModel, Field


class TaxonomyBaseSchema(BaseModel):
    name: str = Field(..., example="taxonomy_name")
    category_id: Optional[str] = Field(None, example="my_category")


class TaxonomyInputSchema(TaxonomyBaseSchema):
    id: Optional[str] = Field(
        None,
        example="my_taxonomy_id",
        description="If id is not provided, generates it as a UUID.",
    )


class JobToTaxonomyAssociationOutSchema(BaseModel):
    job_id: str

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class TaxonomyResponseSchema(TaxonomyInputSchema):
    jobs: List[JobToTaxonomyAssociationOutSchema]
    version: int = Field(description="Version of taxonomy", example=1)

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class JobIdSchemaIn(BaseModel):
    job_id: str = Field(
        ..., example="123abc", description="Job id to link taxonomy to"
    )
    taxonomy_id: str = Field(..., example="my_taxonomy_id")
    taxonomy_version: Optional[int] = Field(
        description="Version of taxonomy", example=1
    )


class CategoryLinkSchema(BaseModel):
    category_id: str = Field(
        ..., example="123abc", description="Job id to link taxonomy to"
    )
    taxonomy_id: str = Field(..., example="my_taxonomy_id")
    taxonomy_version: Optional[int] = Field(
        description="Version of taxonomy", example=1
    )
