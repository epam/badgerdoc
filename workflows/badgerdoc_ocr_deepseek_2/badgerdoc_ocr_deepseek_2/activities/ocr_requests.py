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


HOST = os.environ.get("HOST_ADDRESS", "localhost")
PORT = os.environ.get("PORT", "11434")
MODEL = os.environ.get("DEEPSEEK_2_MODEL", "mlx-community/DeepSeek-OCR-2-bf16")
PROMPT = "<|grounding|>Convert the document to markdown."
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 10000))


@activity.defn
async def deepseek_ocr_from_page(
    extraction_id: int,
    extraction_tags: list[str],
    workflow_type: str,
    page_num: int,
    doc: BadgerdocDocument,
    block_index: int | None = None,
) -> dict[str, Any]:
    """Run DeepSeek OCR-2 on a single page or block-crop image.

    Accepts flattened primitives + single-level BadgerdocDocument instead of
    nested BadgerdocDocumentPage / DocumentTriggerParams — Temporal's default
    JSON converter reconstructs single-level dataclasses correctly but fails
    silently on multi-level nesting, returning a plain dict instead.

    Returns a dict with keys:
        page_num     — the page number (int)
        middle_json  — MinIO path to the raw OCR output JSON
        metadata     — document metadata (width, height, page, position_in_parent)
    """
    import openai  # pylint: disable=import-outside-toplevel

    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
    )

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

    # If the document is already a child doc (rendition or block crop), use its
    # file URL directly — calling get_rendition on a rendition would fail.
    if doc.parent_document_id is not None:
        rendition_doc = doc
    else:
        rendition_doc = await document.badgerdoc_get_rendition(doc, page_num)

    image_url = rendition_doc.file.replace("minio:", "localhost:")
    logger.info(
        "Running DeepSeek OCR on page %d (block_index=%s), image: %s",
        page_num,
        block_index,
        image_url,
    )
    client = openai.OpenAI(
        base_url=f"http://{HOST}:{PORT}/v1", api_key="not-needed"
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
        stream=False,
        max_tokens=MAX_TOKENS,
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
        BytesIO(
            json.dumps({"text": response.choices[0].message.content}).encode()
        ),
        storage_params,
        filename,
    )
    logger.info(
        "DeepSeek OCR complete for page %d (block_index=%s), stored: %s",
        page_num,
        block_index,
        middle_json_path,
    )
    return {
        "page_num": page_num,
        "middle_json": middle_json_path,
        "metadata": rendition_doc.metadata,
    }


@activity.defn
async def deepseek_ocr_merge_and_store(
    workflow_type: str,
    ocr_results: list[dict],
) -> dict[str, str]:
    """Group OCR results by page number and store one manifest per page in MinIO.

    Each entry in ocr_results must contain:
        page_num     — int
        middle_json  — MinIO path to raw OCR output
        metadata     — document metadata dict

    Writes one JSON file per page (page_<N>_manifest.json) containing only
    the infos for that page, so deepseek_ocr_2_results_to_hocr reads a small
    per-page file instead of the entire merged manifest on every call.

    Returns a dict mapping str(page_num) → per-page manifest path in MinIO.
    """
    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
    )

    logger.info(
        "deepseek_ocr_merge_and_store: merging %d OCR results",
        len(ocr_results),
    )

    grouped: dict[str, list[dict]] = {}
    for result in ocr_results:
        page_key = str(result["page_num"])
        grouped.setdefault(page_key, []).append(
            {
                "middle_json": result["middle_json"],
                "metadata": result["metadata"],
            }
        )

    storage_params = storage.StorageWorkflowParams(
        workflow_package="badgerdoc_ocr_deepseek_2",
        workflow_name=workflow_type,
        workflow_id=activity.info().workflow_run_id,
    )

    page_manifest_paths: dict[str, str] = {}
    for page_key, infos in grouped.items():
        manifest_path = await storage.badgerdoc_store_perm(
            BytesIO(json.dumps(infos).encode()),
            storage_params,
            f"page_{page_key}_manifest.json",
        )
        page_manifest_paths[page_key] = manifest_path
        logger.info(
            "deepseek_ocr_merge_and_store: page %s — %d block(s), stored at %s",
            page_key,
            len(infos),
            manifest_path,
        )

    logger.info(
        "deepseek_ocr_merge_and_store: %d page manifest(s) stored",
        len(page_manifest_paths),
    )
    return page_manifest_paths
