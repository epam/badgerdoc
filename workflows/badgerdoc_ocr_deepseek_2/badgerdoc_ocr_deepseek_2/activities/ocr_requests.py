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


HOST = os.environ.get("HOST_ADDRESS_FOR_MLX", "localhost")
PORT = os.environ.get("DEEPSEEK_2_PORT", "11434")
MODEL = os.environ.get("DEEPSEEK_2_MODEL", "mlx-community/DeepSeek-OCR-2-bf16")
PROMPT = "<|grounding|>Convert the document to markdown."
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 10000))


@activity.defn
async def deepseek_prepare_page(
    extraction_id: int,
    extraction_tags: list[str],
    page_num: int,
    doc: BadgerdocDocument,
) -> dict[str, Any]:
    """Resolve the rendition image URL for a page and handle extraction tagging.

    Returns a dict with keys:
        image_url — publicly accessible URL of the page image
        metadata  — document metadata (width, height, page, position_in_parent)
        page_num  — the page number (int)
    """
    if "deepseek-ocr-2" not in extraction_tags:
        logger.info(
            "Adding 'deepseek-ocr-2' tag to extraction %d", extraction_id
        )
        updated_tags = extraction_tags + ["deepseek-ocr-2"]
        await badgerdoc_http.badgerdoc_patch(
            f"/badgerdoc/extraction/{extraction_id}/", {"tags": updated_tags}
        )

    if isinstance(doc, dict):
        doc = BadgerdocDocument(**doc)

    if doc.parent_document_id is not None:
        rendition_doc = doc
    else:
        rendition_doc = await document.badgerdoc_get_rendition(doc, page_num)

    image_url = rendition_doc.file
    logger.info(
        "deepseek_prepare_page: page %d resolved to %s", page_num, image_url
    )
    return {
        "image_url": image_url,
        "metadata": rendition_doc.metadata,
        "page_num": page_num,
    }


@activity.defn
async def deepseek_store_result(
    workflow_type: str,
    page_num: int,
    text: str,
    metadata: dict[str, Any],
    block_index: int | None = None,
) -> dict[str, Any]:
    """Store raw OCR text to MinIO and return the storage path.

    Returns a dict with keys:
        page_num     — the page number (int)
        middle_json  — MinIO path to the raw OCR output JSON
        metadata     — document metadata passed through unchanged
    """
    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
    )

    storage_params = storage.StorageWorkflowParams(
        workflow_package="badgerdoc_ocr_deepseek_2",
        workflow_name=workflow_type,
        workflow_id=activity.info().workflow_run_id,
    )
    filename = (
        f"page_{page_num}_block_{block_index}_middle.json"
        if block_index is not None
        else f"page_{page_num}_middle.json"
    )
    middle_json_path = await storage.badgerdoc_store_perm(
        BytesIO(json.dumps({"text": text}).encode()),
        storage_params,
        filename,
    )
    logger.info(
        "deepseek_store_result: page %d (block_index=%s) stored: %s",
        page_num,
        block_index,
        middle_json_path,
    )
    return {
        "page_num": page_num,
        "middle_json": middle_json_path,
        "metadata": metadata,
    }
