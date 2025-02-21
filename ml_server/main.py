import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from functools import lru_cache

from fastapi import Depends
from gliner import GLiNER

from tenant_dependency import get_tenant_info

KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST", "")
TENANT = get_tenant_info(url=KEYCLOAK_HOST, algorithm="RS256")
ROOT_PATH = os.environ.get("ROOT_PATH", default="")


# Cache will save up to this number of most recently used models. Larger amount will consume more memory,
# but allows more models to be initialized at the same time.
NUM_MODELS_TO_CACHE = 3

def get_version() -> str:
    default = "0.1.0"
    ver = Path(__file__).parent.parent / "version.txt"
    if ver.exists() and ver.is_file():
        with open(ver, "r", encoding="utf-8") as file:
            line = file.readline().strip()
            return line or default

    return default

app = FastAPI(
    title="ML models hosting server",
    version=get_version(),
    root_path=ROOT_PATH,
    dependencies=[Depends(TENANT)])

# Request body model
class PredictionRequest(BaseModel):
    model_id: str
    threshold: float
    labels: List[str]
    text: str


@lru_cache(maxsize=NUM_MODELS_TO_CACHE)
def get_model(model_id: str) -> GLiNER:
    """Download and initialise specified ML model
    
    Args:
        model_id (str): ID of the model to download

    Returns:
        GLiNER: initialized Gliner model
    """
    try:
        # Initialize and cache the model
        model = GLiNER.from_pretrained(model_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model '{model_id}': {str(e)}")
    
    return model


# Named Entity Recognition endpoint
@app.post("/ner")
async def ner(request: PredictionRequest):
    model = get_model(request.model_id)

    # Perform prediction
    try:
        entities = model.predict_entities(request.text, request.labels, threshold=request.threshold)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")

    # Return the prediction results
    return {"entities": entities}

# Run the application with: uvicorn main:app --reload
