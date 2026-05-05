import json
import re
from io import BytesIO

from temporalio import activity

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
    carea_id = par_id = line_id = word_id = 1

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
            words = line_text.split()
            total_chars = sum(len(w) for w in words) or 1
            line_width = x1 - x0

            hocr.append(
                f'  <span class="ocr_line" id="line_{page_number}_{line_id}" title="bbox {x0} {ly0} {x1} {ly1}">'
            )
            line_id += 1

            wx = x0
            for word in words:
                wx1 = wx + round(line_width * len(word) / total_chars)
                hocr.append(
                    f'    <span class="ocrx_word" id="word_{page_number}_{word_id}" '
                    f'title="bbox {wx} {ly0} {wx1} {ly1}">{_escape_html(word)}</span>'
                )
                word_id += 1
                wx = wx1

            hocr.append("  </span>")

        hocr.append("</p>")
        hocr.append("</div>")

    return hocr


@activity.defn
async def deepseek_ocr_2_results_to_hocr(  # pylint: disable=too-many-locals
    workflow_type: str,
    page_num: int,
    infos: list[dict],
) -> BadgerdocHOCRPageResult:
    """Convert DeepSeek OCR raw output for one page (one or more blocks) to hOCR.

    Accepts a list of info dicts so multiple blocks on the same page are merged
    into a single hOCR file keyed by page number. Each info dict contains its
    own metadata.position_in_parent for per-block coordinate remapping.
    """
    # Import storage inside function to avoid startup validation issues
    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
    )

    page_number = page_num

    # Use first info's metadata for page-level dimensions
    first_page_info = (infos[0].get("metadata") or {}) if infos else {}
    page_width = first_page_info.get("width", 0)
    page_height = first_page_info.get("height", 0)
    display_page_num = first_page_info.get("page") or page_number

    storage_params = storage.StorageWorkflowParams(
        workflow_package="badgerdoc_ocr_deepseek_2",
        workflow_name=workflow_type,
        workflow_id=activity.info().workflow_run_id,
    )

    hocr_lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<title></title>",
        '<meta http-equiv="Content-Type" content="text/html;charset=utf-8">',
        "<meta name='ocr-system' content='deepseek-ocr-2'>",
        "<meta name='ocr-capabilities' content='ocr_photo ocr_page ocr_carea ocr_par ocr_line ocrx_word'>",
        "</head>",
        "<body>",
        f'<div class="ocr_page" id="page_{display_page_num}" '
        f'title="bbox 0 0 {page_width} {page_height}; ppageno {display_page_num}">',
    ]

    all_blocks: list[dict] = []
    for info in infos:
        middle_json_path = info.get("middle_json")
        if not middle_json_path:
            raise ValueError(
                f"'middle_json' key missing from OCR activity result for page {page_number}"
            )

        middle_json_buffer = BytesIO()
        await storage.badgerdoc_download(middle_json_buffer, middle_json_path)
        middle_json_buffer.seek(0)
        middle_json = json.load(middle_json_buffer)

        ocr_text: str = middle_json.get("text", "")
        blocks = _parse_ocr_blocks(ocr_text)

        page_info = info.get("metadata") or {}
        position_in_parent: str | None = page_info.get("position_in_parent")
        if position_in_parent:
            cx1, cy1, cx2, cy2 = map(int, position_in_parent.split())
            cw = cx2 - cx1
            ch = cy2 - cy1
            for block in blocks:
                bx1, by1, bx2, by2 = block["bbox"]
                block["bbox"] = (
                    cx1 + round(bx1 * cw / 1000),
                    cy1 + round(by1 * ch / 1000),
                    cx1 + round(bx2 * cw / 1000),
                    cy1 + round(by2 * ch / 1000),
                )

        all_blocks.extend(blocks)

    hocr_lines.extend(_blocks_to_hocr(page_number, all_blocks))
    hocr_lines.extend(["</div>", "</body>", "</html>"])

    hocr_content = "\n".join(hocr_lines)
    hocr_buffer = BytesIO(hocr_content.encode("utf-8"))
    hocr_path = await storage.badgerdoc_store_perm(
        hocr_buffer, storage_params, f"page_{page_number}.hocr"
    )
    return BadgerdocHOCRPageResult(h_ocr={str(page_number): hocr_path})


def _escape_html(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
