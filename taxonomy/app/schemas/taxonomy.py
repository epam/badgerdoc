from typing import List, Optional

from pydantic import BaseModel, Field


class TaxonomyBaseSchema(BaseModel):
    name: str = Field(..., example="taxonomy_name")
    version: int = Field(..., example="1")
    # TODO
    category_id: Optional[str] = Field(None, example="my_category")


class TaxonomyInputSchema(TaxonomyBaseSchema):
    id: Optional[str] = Field(
        None,
        example="my_taxonomy_id",
        description="If id is not provided, generates it as a UUID.",
    )


class TaxonomyResponseSchema(TaxonomyInputSchema):
    parents: List[dict] = Field(default=[])
    is_leaf: Optional[bool] = Field(default=None)

    class Config:
        allow_population_by_field_name = True


class JobIdSchema(BaseModel):
    id: str = Field(..., exclude='123abc')
