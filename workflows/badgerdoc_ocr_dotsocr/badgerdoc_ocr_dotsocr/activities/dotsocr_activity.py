import json
import logging
from io import BytesIO
from typing import TypedDict

from PIL import Image
from temporalio import activity
from temporalio.exceptions import ApplicationError

from badgerdoc_common import badgerdoc_http, hocr, storage, trigger
from badgerdoc_common.activities import document, extraction
from badgerdoc_ocr_dotsocr import hocr_convertion, ocr

logger = logging.getLogger(__name__)


class Outcome(TypedDict):
    json_path: str


@activity.defn
async def dots_ocr_activity(
    params: trigger.DocumentTriggerParams,
) -> Outcome:
    document_to_ocr = params.original_document
    if not document_to_ocr.file:
        raise ApplicationError(
            f"document_to_ocr with id {document_to_ocr.id} does not have file url"
        )

    page_number = params.badgerdoc_trigger_params["page_number"] or 1
    if page_number is None:
        raise ApplicationError(
            "Expected page_number to be provided, received None"
        )

    extraction_obj = params.target_extraction
    current_tags = extraction_obj.tags or []

    if "dots-ocr" not in current_tags:
        logger.info(
            "Adding 'dots-ocr' tag to extraction %s", extraction_obj.id
        )
        await extraction.badgerdoc_update_extraction(
            extraction.UpdateExtractionRequest(
                extraction_id=params.target_extraction.id,
                tags=current_tags + ["dots-ocr"],
            )
        )

    image = await _load_image(document_to_ocr)
    image_width = image.width
    image_height = image.height

    logger.info(
        "Starting image with dimensions w=%d h=%d processing for document: %s",
        image_width,
        image_height,
        document_to_ocr.file,
    )
    ocr_json_text = await ocr.infer_layout(image)

    json_path = await _save_text(
        f"page_{page_number}.json",
        ocr_json_text,
    )
    logger.info("DotsOCR result saved to: %s", json_path)

    return Outcome(json_path=json_path)


@activity.defn
async def convert_to_hocr(
    params: trigger.DocumentTriggerParams,
    raw_result: Outcome,
) -> hocr.BadgerdocHOCRPageResult:
    page_number = params.badgerdoc_trigger_params["page_number"]
    if page_number is None:
        raise ApplicationError(
            "Expected page_number to be provided, received None"
        )

    document_to_ocr = params.original_document
    image_width = (document_to_ocr.metadata or {}).get("width")
    image_height = (document_to_ocr.metadata or {}).get("height")
    if not image_width or not image_height:
        raise ApplicationError(
            f"document_to_ocr with id {document_to_ocr.id} does not have width or height metadata"
        )

    # Need to copy scale logic done in VLLM to avoid skewed coordinates
    image_height, image_width = ocr.resize_to_fit(image_height, image_width)

    buffer = BytesIO()
    await storage.badgerdoc_download(buffer, raw_result["json_path"])
    buffer.seek(0)
    layout = hocr_convertion.LayoutResponse.model_validate(
        json.loads(buffer.read().decode("utf-8"))
    )

    hocr_text = layout.to_hocr(
        page_number=page_number,
        width=image_width,
        height=image_height,
    )
    hocr_path = await _save_text(
        f"page_{page_number}.hocr",
        hocr_text,
    )
    logger.info("DotsOCR hOCR result saved to: %s", hocr_path)

    return hocr.BadgerdocHOCRPageResult(h_ocr={page_number: hocr_path})


async def _load_image(
    image_document: document.BadgerdocDocument,
) -> Image.Image:
    buffer = BytesIO()
    await badgerdoc_http.badgerdoc_download(buffer, image_document)

    buffer.seek(0)
    image = Image.open(buffer)
    return ocr.prepare_image(image)


async def _save_text(file_name: str, text: str) -> str:
    storage_params = storage.StorageWorkflowParams(
        workflow_package="badgerdoc_ocr_dotsocr",
        workflow_name="BadgerdocOCRDotsOCRWorkflow",
        workflow_id=activity.info().workflow_id or "",
    )
    file_path = storage.build_temp_path(storage_params, file_name)

    buffer = BytesIO(text.encode("utf-8"))
    await storage.badgerdoc_store(buffer, file_path)
    return file_path
