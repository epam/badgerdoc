import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from gliner import GLiNER
from pydantic import BaseModel, Field
from tenant_dependency import get_tenant_info

KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST", "")
TENANT = get_tenant_info(url=KEYCLOAK_HOST, algorithm="RS256")
ROOT_PATH = os.environ.get("ROOT_PATH", default="")


# Cache will save up to this number of most recently used models.
# Larger amount will consume more memory,
# but allows more models to be initialized at the same time.
NUM_MODELS_TO_CACHE = 3


def get_version() -> str:
    default = "0.1.0"
    ver = Path(__file__).parent / "version.txt"
    if ver.exists() and ver.is_file():
        with open(ver, "r", encoding="utf-8") as file:
            line = file.readline().strip()
            return line or default

    return default


app = FastAPI(
    title="ML models hosting server",
    version=get_version(),
    root_path=ROOT_PATH,
    dependencies=[Depends(TENANT)],
)


class PredictionRequest(BaseModel):
    """Request body model"""

    model_id: str
    threshold: Annotated[float, Field(ge=0, le=1)]
    labels: list[str]
    text: str


class Entity(BaseModel):
    """Represents one entity extracted from the text"""

    start: int
    end: int
    text: str
    label: str


class GlinerResponse(BaseModel):
    entities: list[Entity]


@lru_cache(maxsize=NUM_MODELS_TO_CACHE)
def get_model(model_id: str) -> GLiNER:
    """Download and initialise specified ML model

    Args:
        model_id (str): ID of the model to download

    Returns:
        GLiNER: initialized Gliner model
    """
    try:
        model = GLiNER.from_pretrained(model_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load model model_id({model_id})",
        ) from e
    return model


@app.post("/ner")
async def named_entity_recognition(
    request: PredictionRequest,
) -> GlinerResponse:
    model = get_model(request.model_id)
    try:
        entities = model.predict_entities(
            request.text, request.labels, threshold=request.threshold
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error occured while entities extraction"
        ) from e
    return {"entities": entities}
