import json
import logging
import os
from io import BytesIO
from typing import Any

from temporalio import activity

from badgerdoc_common import badgerdoc_http
from badgerdoc_common.activities import document
from badgerdoc_common.activities.document import BadgerdocDocument


@activity.defn
async def mineru_mlx_tag_extraction(
    extraction_id: int,
    extraction_tags: list[str],
) -> None:
    """Ensure the 'mineru-mlx' tag is present on the extraction. Called once before fan-out."""
    if "mineru-mlx" not in extraction_tags:
        logger.info("Adding 'mineru-mlx' tag to extraction %d", extraction_id)
        await badgerdoc_http.badgerdoc_patch(
            f"/badgerdoc/extraction/{extraction_id}/",
            {"tags": extraction_tags + ["mineru-mlx"]},
        )


logger = logging.getLogger(__name__)

HOST = os.environ.get("HOST_ADDRESS", "localhost")
PORT = os.environ.get("MINERU_MLX_PORT", "11436")
MODEL = os.environ.get(
    "MINERU_MLX_MODEL", "mlx-community/MinerU2.5-2509-1.2B-bf16"
)


@activity.defn
async def mineru_mlx_ocr_page(
    workflow_type: str,
    page_num: int,
    doc: BadgerdocDocument,
    block_index: int | None = None,
) -> dict[str, Any]:
    """Run MinerU MLX two-step OCR on a single page or block-crop image.

    Uses mineru-vl-utils MinerUClient with backend="http-client" to perform
    layout detection + per-block content recognition. Returns real bounding
    box coordinates (normalized [0, 1]) alongside the extracted content.

    Returns a dict with keys:
        page_num     — the page number (int)
        middle_json  — MinIO path to JSON containing extracted blocks
        metadata     — document metadata (width, height, page, position_in_parent)
    """
    from mineru_vl_utils import MinerUClient
    from PIL import Image

    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
    )

    if isinstance(doc, dict):
        doc = BadgerdocDocument(**doc)

    if doc.parent_document_id is not None:
        rendition_doc = doc
    else:
        rendition_doc = await document.badgerdoc_get_rendition(doc, page_num)

    logger.info(
        "MinerU MLX OCR: starting page %d (block_index=%s), image: %s",
        page_num,
        block_index,
        rendition_doc.file,
    )

    img_buf = BytesIO()
    await badgerdoc_http.badgerdoc_download(img_buf, rendition_doc)
    image = Image.open(img_buf)

    client = MinerUClient(
        backend="http-client",
        model_name=MODEL,
        server_url=f"http://{HOST}:{PORT}",
    )
    result = await client.aio_two_step_extract(image)

    blocks = [
        {"type": b["type"], "bbox": b["bbox"], "content": b["content"] or ""}
        for b in result
    ]
    logger.info(
        "MinerU MLX OCR: page %d (block_index=%s) — %d block(s) detected",
        page_num,
        block_index,
        len(blocks),
    )

    storage_params = storage.StorageWorkflowParams(
        workflow_package="badgerdoc_ocr_mineru",
        workflow_name=workflow_type,
        workflow_id=activity.info().workflow_run_id,
    )
    filename = (
        f"page_{page_num}_block_{block_index}_middle.json"
        if block_index is not None
        else f"page_{page_num}_middle.json"
    )
    middle_json_path = await storage.badgerdoc_store_perm(
        BytesIO(json.dumps({"blocks": blocks}).encode()),
        storage_params,
        filename,
    )
    logger.info(
        "MinerU MLX OCR: page %d (block_index=%s) complete, stored: %s",
        page_num,
        block_index,
        middle_json_path,
    )
    return {
        "page_num": page_num,
        "middle_json": middle_json_path,
        "metadata": rendition_doc.metadata,
    }
