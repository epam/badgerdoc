import json
import logging
import os
import re
from io import BytesIO

from bs4 import BeautifulSoup
from PIL import Image, ImageOps, UnidentifiedImageError
from temporalio import activity

from badgerdoc_common import trigger
from badgerdoc_common.activities import agent_log, document
from badgerdoc_common.activities.extraction import (
    ListExtractionPagesRequest,
    badgerdoc_get_extraction,
    badgerdoc_list_extraction_pages,
)
from badgerdoc_common.badgerdoc_http import badgerdoc_download, badgerdoc_patch
from badgerdoc_common.hocr import BadgerdocHOCRPageResult

Image.MAX_IMAGE_PIXELS = 933120000

logger = logging.getLogger(__name__)

MAX_REQUEST_IMAGE_BYTES = 3 * 1024 * 1024
MAX_IMAGE_SIDE_PX = 8000


_JURY_SYSTEM_PROMPT = (
    "You are given results from different OCR engines or from just one.\n"
    "Your evaluation should focus on the precision of the extracted text.\n"
    "Provide short analysis and score every text block from 0 to 100, where 100 is the best OCR"
    " results.\n"
    "Also, pay close attention to the accuracy of the extracted text especially subscripts, superscripts and registered marks."
)

_OCR_JUDGE_SYSTEM_PROMPT = (
    "You are an OCR process judge.\n"
    "Your task is to produce the best OCR result using other OCR engines output and the source image"
    " in hOCR format and evaluation report."
)

_HOCR_EXTRACTION_PROMPT = (
    "Compare OCR results given in dictionary format and produce the best possible OCR result using the source image as a reference.\n"
    "Combine best blocks from different engines by choosing right key-value pairs based on the jury text evaluation and return result in same format.\n"
    "If higher scored OCR engine is missing some blocks that are present in lower scored engine result, include these blocks in the final result.\n"
    "Pay close attention to the accuracy of the extracted text especially subscripts, superscripts and registered marks.\n"
    "Be sure to highlight subscripts and superscripts using LaTeX notation or mark like this`^{*1,2}`, `^{*}`.\n"
    "Do not include page dimension metadata.\n"
    "DO NOT change any keys in dictionary.\n"
)

_OCR_CLERK_SYSTEM_PROMPT = (
    "You are pedantic and precise worker.\n"
    "Your task is to take OCR results in hOCR format sort them in human readable order,\n"
    " and classify text blocks according to source image formatting."
)

_HOCR_SORTING_AND_CLASSIFICATION_PROMPT = (
    "Sort hOCR blocks from top to bottom and from left to right adjusting blocks ids where first digit it is page number.\n"
    "Classify text blocks according to the following rules:\n"
    "1) If block contains an unordered list add <ul> and <li> tags accordingly.\n"
    "2) If block contains bold, italic or underlined text add <b>, <i> or <u> tags accordingly.\n"
    "3) If block contains multiple lines add <br> tag at the end of each line.\n"
    "4) Make sure to wrap all subscript and superscript text in <sub> and <sup> tags accordingly.\n"
    "Output only the final hOCR content without any explanations."
)


def compress_image_for_llm_request(
    image_bytes: bytes,
    max_bytes: int = MAX_REQUEST_IMAGE_BYTES,
    max_side_px: int = MAX_IMAGE_SIDE_PX,
) -> tuple[bytes, int, int]:
    """Compress an image so byte size and dimensions fit request limits.

    Returns:
        (compressed_bytes, sent_width, sent_height)
    """
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            converted: Image.Image = ImageOps.exif_transpose(img).convert(
                "RGB"
            )
            width, height = converted.size

            if (
                width <= max_side_px
                and height <= max_side_px
                and len(image_bytes) <= max_bytes
            ):
                return image_bytes, width, height

            if width > max_side_px or height > max_side_px:
                scale_to_limit = min(max_side_px / width, max_side_px / height)
                converted = converted.resize(
                    (
                        max(1, int(width * scale_to_limit)),
                        max(1, int(height * scale_to_limit)),
                    ),
                    Image.Resampling.LANCZOS,
                )
                width, height = converted.size

            scale_steps = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
            quality_steps = [90, 80, 70, 60, 50, 40, 30]
            best_candidate = b""
            best_w, best_h = width, height

            for scale in scale_steps:
                scaled = converted
                sw, sh = width, height
                if scale < 1.0:
                    sw = max(1, int(width * scale))
                    sh = max(1, int(height * scale))
                    scaled = converted.resize(
                        (sw, sh), Image.Resampling.LANCZOS
                    )
                for _ in quality_steps:
                    out = BytesIO()
                    scaled.save(
                        out,
                        format="PNG",
                        optimize=True,
                    )
                    candidate = out.getvalue()
                    if not best_candidate or len(candidate) < len(
                        best_candidate
                    ):
                        best_candidate = candidate
                        best_w, best_h = sw, sh
                    if len(candidate) <= max_bytes:
                        return candidate, sw, sh

            activity.logger.warning(
                "Unable to compress image below %s bytes;"
                " sending smallest candidate of %s bytes",
                max_bytes,
                len(best_candidate),
            )
            return best_candidate, best_w, best_h

    except (UnidentifiedImageError, OSError) as exc:
        activity.logger.warning(
            "Could not parse image for compression,"
            " sending original payload: %s",
            exc,
        )
        with Image.open(BytesIO(image_bytes)) as img:
            w, h = img.size
        return image_bytes, w, h


def extract_text_from_hocr(
    hocr_content: str, preserve_layout: bool = False
) -> str:
    """
    Extract text from hOCR HTML content.
    """
    soup = BeautifulSoup(hocr_content, "html.parser")
    lines = soup.find_all("span", class_="ocr_line")
    if not lines:
        return ""
    text_lines = [line.get_text(separator=" ", strip=True) for line in lines]
    return "\n".join(text_lines) if preserve_layout else " ".join(text_lines)


def hocr_page_to_html(
    body_html: str, page_width: int, page_height: int, page_num: int
) -> str:
    header = (
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'
        ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" lang="en">\n'
        "<head>\n"
        "<title></title>\n"
        '<meta http-equiv="content-type" content="text/html; charset=utf-8" />\n'
        '<meta name="ocr-system" content="dial-ocr" />\n'
        '<meta name="ocr-capabilities"'
        ' content="ocr_page ocr_carea ocr_par ocr_header ocr_line" />\n'
        '<meta name="ocr-langs" content="en" />\n'
        "</head>\n"
        "<body>\n"
        f'<div class="ocr_page" id="page_{page_num}"'
        f' title="bbox 0 0 {page_width} {page_height}; ppageno {page_num - 1}">\n'
    )
    footer = "\n</div>\n</body>\n</html>"
    return header + body_html.strip() + footer


_BBOX_RE = re.compile(r"bbox\s+(\d+\s+\d+\s+\d+\s+\d+)")


def extract_elements_from_hocr(
    hocr_content: str,
) -> dict[str, str]:
    """Parse hOCR HTML into a dict of lines."""
    soup = BeautifulSoup(hocr_content, "html.parser")
    result: dict[str, str] = {}
    for line in soup.find_all(class_="ocr_line"):
        title = line.get("title", "")
        m = _BBOX_RE.search(title)
        if m:
            result[m.group(1)] = line.get_text(separator=" ", strip=True)
    return result


def _escape_html(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def lines_to_hocr(
    lines: dict[str, str],
    page_number: int,
) -> str:
    """Convert a bbox→text dict back into an hOCR body fragment."""
    parts: list[str] = []
    for idx, (bbox, text) in enumerate(lines.items(), start=1):
        block_id = f"block_{page_number}_{idx}"
        par_id = f"par_{page_number}_{idx}"
        x0, y0, x1, y1 = map(int, bbox.split())
        line_height = y1 - y0
        parts.append(
            f'<div class="ocr_carea" id="{block_id}" title="bbox {bbox}">'
        )
        parts.append(f'<p class="ocr_par" id="{par_id}" title="bbox {bbox}">')
        line_id = 1
        if text:
            li_elem_id = f"line_{block_id}_{line_id}"
            for i, text in enumerate(text.splitlines()):
                ly0 = round(y0 + i * line_height)
                ly1 = round(y0 + (i + 1) * line_height)
                parts.append(
                    f'<span class="ocr_line" id="{li_elem_id}" title="bbox'
                    f' {x0} {ly0} {x1} {ly1}">{_escape_html(text)}</span>'
                )
            line_id += 1

        parts.append("</p>")
        parts.append("</div>")
    return "\n".join(parts)


@activity.defn
async def trial_process(
    params: trigger.DocumentTriggerParams,
    workflow_results: list[dict[str, int | str]],
) -> BadgerdocHOCRPageResult:
    from openai import (  # pylint: disable=import-outside-toplevel
        AsyncAzureOpenAI,
    )
    from pydantic_ai import (  # pylint: disable=import-outside-toplevel
        Agent,
        BinaryContent,
    )
    from pydantic_ai.models.openai import (  # pylint: disable=import-outside-toplevel
        OpenAIChatModel,
    )
    from pydantic_ai.providers.openai import (  # pylint: disable=import-outside-toplevel
        OpenAIProvider,
    )

    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
    )

    document_id = params.original_document.id
    task_id = params.original_task.id if params.original_task else None

    extraction_obj = params.target_extraction
    current_tags = extraction_obj.tags or []

    if "ocr-arbitrator" not in current_tags:
        logger.info(
            "Adding 'ocr-arbitrator' tag to extraction %s", extraction_obj.id
        )
        updated_tags = current_tags + ["ocr-arbitrator"]
        endpoint = f"/badgerdoc/extraction/{extraction_obj.id}/"
        await badgerdoc_patch(endpoint, {"tags": updated_tags})

    target_page = None
    if params.linked_document_pages:
        target_page = params.linked_document_pages[0]

    page_number = target_page.page_num if target_page else 1
    document_to_ocr = await document.badgerdoc_get_rendition(
        target_page.document if target_page else params.original_document,
        page_number,
    )

    ocr_results: dict[str, str] = {}
    ocr_results_with_layout: dict[str, dict[str, str]] = {}
    for workflow_result in workflow_results:
        extraction_id = workflow_result.get("extraction_id")
        engine_name = workflow_result.get("engine_name")
        if not isinstance(extraction_id, int) or not isinstance(
            engine_name, str
        ):
            logger.warning(
                "Skipping invalid workflow result payload: %s",
                workflow_result,
            )
            continue

        extraction = await badgerdoc_get_extraction(extraction_id)
        extraction_page = await badgerdoc_list_extraction_pages(
            ListExtractionPagesRequest(
                extraction_id=int(extraction.id),
                page_number=page_number,
            )
        )
        if not extraction_page.extraction_pages:
            activity.logger.warning(
                "No extraction pages found for extraction_id=%s,"
                " page_number=%s",
                extraction.id,
                page_number,
            )
            continue
        text = extract_text_from_hocr(
            extraction_page.extraction_pages[0].content
        )
        ocr_results[engine_name] = text
        blocks = extract_elements_from_hocr(
            extraction_page.extraction_pages[0].content
        )
        ocr_results_with_layout[engine_name] = blocks

    if not ocr_results:
        return BadgerdocHOCRPageResult(h_ocr={})

    openai_client = AsyncAzureOpenAI(
        api_key=os.environ.get("ARBITRATOR_API_KEY"),
        azure_endpoint="https://ai-proxy.lab.epam.com",
        api_version="2024-02-01",
    )
    model = OpenAIChatModel(
        os.environ.get("JUDGE_MODEL"),
        provider=OpenAIProvider(openai_client=openai_client),
    )

    storage_params = storage.StorageWorkflowParams(
        workflow_package="badgerdoc_ocr_arbitrator",
        workflow_name=params.workflow.temporal_workflow_type,
        workflow_id=activity.info().workflow_run_id,
    )

    # --- Step 1: Jury evaluation of OCR results ---
    await agent_log.write_agent_log(
        document_id,
        task_id,
        "INFO",
        "Temporal",
        {"message": "Step 1: Jury evaluation of OCR results"},
    )
    jury_agent: Agent[None, str] = Agent(
        model,
        instructions=_JURY_SYSTEM_PROMPT,
        output_type=str,
    )

    ocr_summary = "\n".join(
        f"OCR engine: {name}, Discovery result: {blocks}"
        for name, blocks in ocr_results.items()
    )
    jury_result = await jury_agent.run(ocr_summary)
    evaluation_text = jury_result.output

    middle_json_path = await storage.badgerdoc_store_perm(
        BytesIO(json.dumps({"text": evaluation_text}, indent=4).encode()),
        storage_params,
        "middle.json",
    )
    logger.info("Jury evaluation report stored at %s", middle_json_path)

    metadata = document_to_ocr.metadata or {}
    page_width: int = metadata.get("width", 1000)
    page_height: int = metadata.get("height", 1000)

    # --- Step 2: OCR combination with judge ---
    await agent_log.write_agent_log(
        document_id,
        task_id,
        "INFO",
        "Temporal",
        {"message": "Step 2: OCR combination with judge"},
    )

    buffer = BytesIO()
    await badgerdoc_download(buffer, document_to_ocr)
    compressed_bytes, _, _ = compress_image_for_llm_request(buffer.getvalue())

    ocr_judge_agent: Agent[None, dict] = Agent(
        model,
        instructions=_OCR_JUDGE_SYSTEM_PROMPT,
        output_type=dict,
    )

    ocr_context = "\n".join(
        f"OCR engine: {name}, OCR result: {blocks}"
        for name, blocks in ocr_results_with_layout.items()
    )

    judge_result = await ocr_judge_agent.run(
        [
            f"Use jury evaluation report to improve OCR results:"
            f" {evaluation_text}",
            ocr_context,
            _HOCR_EXTRACTION_PROMPT,
            BinaryContent(data=compressed_bytes, media_type="image/png"),
        ]
    )

    hocr_body = lines_to_hocr(judge_result.output, page_number)
    hocr_content = hocr_page_to_html(
        hocr_body, page_width, page_height, page_number
    )

    hocr_buffer = BytesIO(hocr_content.encode("utf-8"))
    hocr_path = await storage.badgerdoc_store_perm(
        hocr_buffer, storage_params, f"middle_{page_number}.hocr"
    )
    hocr_buffer.seek(0)
    hocr_buffer.truncate(0)
    # --- Step 3: Sorting and classification of hOCR content ---
    await agent_log.write_agent_log(
        document_id,
        task_id,
        "INFO",
        "Temporal",
        {"message": "Step 3: Sorting and classification of hOCR content"},
    )

    ocr_clerk_agent: Agent[None, str] = Agent(
        model,
        instructions=_OCR_CLERK_SYSTEM_PROMPT,
        output_type=str,
    )

    clerk_result = await ocr_clerk_agent.run(
        [
            f"Evaluated hOCR content:" f" {hocr_content}",
            f"Page number: {page_number}",
            _HOCR_SORTING_AND_CLASSIFICATION_PROMPT,
            BinaryContent(data=compressed_bytes, media_type="image/png"),
        ]
    )

    hocr_buffer = BytesIO(clerk_result.output.encode("utf-8"))
    hocr_path = await storage.badgerdoc_store_perm(
        hocr_buffer, storage_params, f"page_{page_number}.hocr"
    )
    await agent_log.write_agent_log(
        document_id,
        task_id,
        "INFO",
        "Temporal",
        {"message": "Arbitration trial completed and stored"},
    )

    return BadgerdocHOCRPageResult(h_ocr={page_number: hocr_path})
