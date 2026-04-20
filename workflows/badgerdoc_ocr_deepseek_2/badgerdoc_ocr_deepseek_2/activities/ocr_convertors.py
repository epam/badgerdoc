import json
import re
from io import BytesIO

from temporalio import activity

from badgerdoc_common import trigger
from badgerdoc_common.hocr import BadgerdocHOCRPageResult

_BLOCK_RE = re.compile(
    r"<\|ref\|>(.*?)<\|/ref\|>"
    r"<\|det\|>\[\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]\]<\|/det\|>"
    r"\n(.*?)(?=<\|ref\|>|\Z)",
    re.DOTALL,
)
_HEADING_RE = re.compile(r"^#{1,6}\s*")


def _parse_ocr_blocks(text: str) -> list[dict]:
    blocks = []
    for m in _BLOCK_RE.finditer(text):
        ref_type = m.group(1)
        x0, y0, x1, y1 = (
            int(m.group(2)),
            int(m.group(3)),
            int(m.group(4)),
            int(m.group(5)),
        )
        raw = m.group(6)
        lines = []
        for line in raw.splitlines():
            line = _HEADING_RE.sub("", line).strip()
            if line:
                lines.append(line)
        if lines:
            blocks.append(
                {"type": ref_type, "bbox": (x0, y0, x1, y1), "lines": lines}
            )
    return blocks


def _blocks_to_hocr(  # pylint: disable=too-many-locals
    page_number: int,
    blocks: list[dict],
) -> list[str]:
    hocr: list[str] = []
    carea_id = par_id = line_id = 1

    for block in blocks:
        x0, y0, x1, y1 = block["bbox"]
        lines = block["lines"]
        n_lines = len(lines)
        line_height = (y1 - y0) / n_lines if n_lines else (y1 - y0)

        hocr.append(
            f'<div class="ocr_carea" id="block_{page_number}_{carea_id}" title="bbox {x0} {y0} {x1} {y1}">'
        )
        carea_id += 1

        hocr.append(
            f'<p class="ocr_par" id="par_{page_number}_{par_id}" title="bbox {x0} {y0} {x1} {y1}">'
        )
        par_id += 1

        for i, line_text in enumerate(lines):
            ly0 = round(y0 + i * line_height)
            ly1 = round(y0 + (i + 1) * line_height)

            hocr.append(
                f'  <span class="ocr_line" id="line_{page_number}_{line_id}" title="bbox {x0} {ly0} {x1} {ly1}">'
                f"{_escape_html(line_text)}</span>"
            )
            line_id += 1

        hocr.append("</p>")
        hocr.append("</div>")

    return hocr


@activity.defn
async def deepseek_ocr_2_results_to_hocr(  # pylint: disable=too-many-locals
    params: trigger.DocumentTriggerParams,
    info: dict,
) -> BadgerdocHOCRPageResult:
    # Import storage inside function to avoid startup validation issues
    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
    )

    page_info = info.get("metadata") or {}

    page_number = params.badgerdoc_trigger_params.get("page_number")
    if page_number is None:
        raise ValueError(
            "page_number is required in badgerdoc_trigger_params for hOCR conversion"
        )

    storage_params = storage.StorageWorkflowParams(
        workflow_package="badgerdoc_ocr_deepseek_2",
        workflow_name=params.workflow.temporal_workflow_type,
        workflow_id=activity.info().workflow_run_id,
    )
    middle_json_buffer = BytesIO()
    await storage.badgerdoc_download_perm(
        middle_json_buffer, storage_params, "middle.json"
    )
    middle_json_buffer.seek(0)
    middle_json = json.load(middle_json_buffer)

    ocr_text: str = middle_json.get("text", "")

    page_num = page_info.get("page", 0)
    page_width = page_info.get("width", 0)
    page_height = page_info.get("height", 0)

    hocr_lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<title></title>",
        '<meta http-equiv="Content-Type" content="text/html;charset=utf-8">',
        "<meta name='ocr-system' content='deepseek-ocr-2'>",
        "<meta name='ocr-capabilities' content='ocr_page ocr_carea ocr_par ocr_line'>",
        "</head>",
        "<body>",
        f'<div class="ocr_page" id="page_{page_num}" '
        f'title="bbox 0 0 {page_width} {page_height}; ppageno {page_num}">',
    ]

    blocks = _parse_ocr_blocks(ocr_text)
    hocr_lines.extend(_blocks_to_hocr(page_number, blocks))

    hocr_lines.extend(["</div>", "</body>", "</html>"])

    hocr_content = "\n".join(hocr_lines)

    hocr_buffer = BytesIO(hocr_content.encode("utf-8"))
    hocr_path = await storage.badgerdoc_store_perm(
        hocr_buffer, storage_params, f"page_{page_number}.hocr"
    )
    return BadgerdocHOCRPageResult(h_ocr={page_number: hocr_path})


def _escape_html(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
