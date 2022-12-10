from typing import Dict

from fastapi import APIRouter, status

from src.logger import get_logger
from src.vertex_to_bd.converter import (
    PDFRenderer,
    PlainTextToBadgerdocTokenConverter,
    VertexToBDConvertUseCase,
)
from src.vertex_to_bd.models import VertexRequest
from src.config import minio_client, settings


router = APIRouter(prefix="/vertex", tags=["vertex"])
LOGGER = get_logger(__file__)


@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
)
def import_vertex(request: VertexRequest) -> Dict[str, int]:
    page_border_offset = 15  # TODO
    plain_text_converter = PlainTextToBadgerdocTokenConverter(
        page_border_offset=page_border_offset
    )
    pdf_renderer = PDFRenderer(page_border_offset=page_border_offset)

    vertext_to_bd_use_case = VertexToBDConvertUseCase(
        plain_text_converter=plain_text_converter, pdf_renderer=pdf_renderer, s3_client=minio_client
    )
    vertext_to_bd_use_case.execute(
        s3_input_annotation=request.input_annotation,
        s3_output_pdf=request.output_pdf,
        s3_output_tokens=request.output_tokens,
        s3_output_annotation=request.output_annotation,
    )

    return {"status": status.HTTP_201_CREATED}
