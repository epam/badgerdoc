from typing import Optional

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


class TaxonomyResponseSchema(TaxonomyInputSchema):
    version: int = Field(description="Version of taxonomy", example=1)

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class JobIdSchema(BaseModel):
    id: str = Field(..., example="123abc")
