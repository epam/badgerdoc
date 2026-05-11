import json
import logging
import os
from io import BytesIO
from typing import Any

from temporalio import activity

from badgerdoc_common import badgerdoc_http
from badgerdoc_common.activities import document
from badgerdoc_common.activities.document import BadgerdocDocument

logger = logging.getLogger(__name__)

PORT = os.environ.get("MINERU_MLX_PORT", "11436")
MODEL = os.environ.get(
    "MINERU_MLX_MODEL", "mlx-community/MinerU2.5-2509-1.2B-bf16"
)


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


@activity.defn
async def mineru_prepare_page(
    page_num: int,
    doc: BadgerdocDocument,
) -> dict[str, Any]:
    """Resolve the rendition image URL for a page.

    Returns a dict with keys:
        image_url — publicly accessible URL of the page image
        metadata  — document metadata (width, height, page, position_in_parent)
    """
    if isinstance(doc, dict):
        doc = BadgerdocDocument(**doc)

    if doc.parent_document_id is not None:
        rendition_doc = doc
    else:
        rendition_doc = await document.badgerdoc_get_rendition(doc, page_num)

    image_url = rendition_doc.file
    logger.info(
        "mineru_prepare_page: page %d resolved to %s", page_num, image_url
    )
    return {
        "image_url": image_url,
        "metadata": rendition_doc.metadata,
    }


@activity.defn
async def mineru_store_result(
    workflow_type: str,
    page_num: int,
    blocks: list[dict],
    metadata: dict[str, Any],
    block_index: int | None = None,
) -> dict[str, Any]:
    """Store MinerU OCR blocks to MinIO and return the storage path.

    Returns a dict with keys:
        page_num     — the page number (int)
        middle_json  — MinIO path to the JSON containing extracted blocks
        metadata     — document metadata passed through unchanged
    """
    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
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
        "mineru_store_result: page %d (block_index=%s) stored: %s",
        page_num,
        block_index,
        middle_json_path,
    )
    return {
        "page_num": page_num,
        "middle_json": middle_json_path,
        "metadata": metadata,
    }
