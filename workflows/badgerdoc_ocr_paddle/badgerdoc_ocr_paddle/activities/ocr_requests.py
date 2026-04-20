import json
import logging
import os
from io import BytesIO
from typing import Any

from temporalio import activity

from badgerdoc_common import badgerdoc_http, trigger

logger = logging.getLogger(__name__)


HOST = os.environ.get("HOST_ADDRESS", "localhost")
PORT = os.environ.get("PORT", "11435")
MODEL = os.environ.get("PADDLE_MODEL", "mlx-community/PaddleOCR-VL-1.5-bf16")
PROMPT = "Spotting:"
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 10000))


@activity.defn
async def paddle_ocr(
    params: trigger.DocumentTriggerParams,
) -> dict[str, Any]:
    # Import modules inside function to avoid Temporal startup validation issues
    import openai  # pylint: disable=import-outside-toplevel

    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
    )

    extraction_obj = params.new_extraction
    current_tags = extraction_obj.tags or []

    if "paddle-ocr" not in current_tags:
        logger.info(
            "Adding 'paddle-ocr' tag to extraction %s", extraction_obj.id
        )
        updated_tags = current_tags + ["paddle-ocr"]
        endpoint = f"/badgerdoc/extraction/{extraction_obj.id}/"
        await badgerdoc_http.badgerdoc_patch(endpoint, {"tags": updated_tags})

    document = params.document_to_ocr
    image_url = document.file.replace("minio:", "localhost:")
    logger.info("Document file downloaded successfully")
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
        workflow_package="badgerdoc_ocr_paddle",
        workflow_name=params.workflow.temporal_workflow_type,
        workflow_id=activity.info().workflow_run_id,
    )
    middle_json_path = await storage.badgerdoc_store_perm(
        BytesIO(
            json.dumps({"text": response.choices[0].message.content}).encode()
        ),
        storage_params,
        "middle.json",
    )
    return {"middle_json": middle_json_path, "metadata": document.metadata}
