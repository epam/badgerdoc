from typing import Dict

from fastapi import APIRouter, status, HTTPException

from src.config import minio_client
from src.logger import get_logger
from src.vertex_to_bd.badgerdoc_to_vertex_use_case import (
    BDToVertexConvertUseCase,
)
from src.vertex_to_bd.vertex_to_badgerdoc_use_case import VertexToBDConvertUseCase
from src.vertex_to_bd.models import VertexRequest
from src.vertex_to_bd.models.vertex_models import BadgerdocToVertexRequest

router = APIRouter(prefix="/vertex", tags=["vertex"])
LOGGER = get_logger(__file__)


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
)
def import_vertex(request: VertexRequest) -> Dict[str, int]:
    try:
        vertext_to_bd_use_case = VertexToBDConvertUseCase(
            s3_client=minio_client,
        )
        vertext_to_bd_use_case.execute(
            s3_input_annotation=request.input_annotation,
            s3_output_pdf=request.output_pdf,
            s3_output_tokens=request.output_tokens,
            s3_output_annotations=request.output_annotation,
        )
    except Exception as exp:
        raise HTTPException(status_code=500, detail=str(exp))
    return {"status": status.HTTP_201_CREATED}


@router.post(
    "/export",
    status_code=status.HTTP_201_CREATED,
)
def export_vertex(request: BadgerdocToVertexRequest) -> Dict[str, int]:
    try:
        bd_to_vertex_use_case = BDToVertexConvertUseCase(
            s3_client=minio_client,
        )
        bd_to_vertex_use_case.execute(
            s3_input_tokens=request.input_tokens,
            s3_input_annotations=request.input_annotation,
            s3_output_annotation=request.output_annotation,
        )
    except Exception as exp:
        raise HTTPException(status_code=500, detail=str(exp))
    return {"status": status.HTTP_201_CREATED}
