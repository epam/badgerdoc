import json
import logging
import os
from io import BytesIO
from typing import Any

from temporalio import activity

from badgerdoc_common import badgerdoc_http, trigger
from badgerdoc_common.activities import document
from badgerdoc_common.activities.document import (
    BadgerdocDocument,
    DocumentChunkRequest,
    badgerdoc_get_document_chunk,
)

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
    """
    # Import modules inside function to avoid Temporal startup validation issues
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
        "middle_json": middle_json_path,
        "metadata": rendition_doc.metadata,
    }


@activity.defn
async def deepseek_ocr_from_block(
    params: trigger.DocumentTriggerParams,
    page: trigger.BadgerdocDocumentPage,
    xpath: str,
    extraction_id: int,
    block_id: str,
) -> dict[str, Any]:
    import openai  # pylint: disable=import-outside-toplevel

    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
    )

    extraction_obj = params.target_extraction
    current_tags = extraction_obj.tags or []

    if "deepseek-ocr-2" not in current_tags:
        logger.info(
            "Adding 'deepseek-ocr-2' tag to extraction %s", extraction_obj.id
        )
        updated_tags = current_tags + ["deepseek-ocr-2"]
        endpoint = f"/badgerdoc/extraction/{extraction_obj.id}/"
        await badgerdoc_http.badgerdoc_patch(endpoint, {"tags": updated_tags})

    chunk_doc = await badgerdoc_get_document_chunk(
        DocumentChunkRequest(
            document_id=params.original_document.id,
            page_num=page.page_num,
            extraction_id=extraction_id,
            xpath=xpath,
        )
    )
    image_url = chunk_doc.file.replace("minio:", "localhost:")
    logger.info("Chunk document retrieved for xpath: %s", xpath)

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
        workflow_name=params.workflow.temporal_workflow_type,
        workflow_id=activity.info().workflow_run_id,
    )
    middle_json_path = await storage.badgerdoc_store_perm(
        BytesIO(
            json.dumps({"text": response.choices[0].message.content}).encode()
        ),
        storage_params,
        f"page_{page.page_num}_{block_id}.json",
    )
    return {
        "middle_json": middle_json_path,
        "metadata": chunk_doc.metadata,
        "block_id": block_id,
    }
