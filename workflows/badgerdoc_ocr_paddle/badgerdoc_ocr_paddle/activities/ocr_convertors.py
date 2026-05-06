import json
import logging
import re
from io import BytesIO

import markdown as md_lib
from lxml import etree
from temporalio import activity

from badgerdoc_common.hocr import BadgerdocHOCRPageResult

logger = logging.getLogger(__name__)

_BLOCK_RE = re.compile(
    r"<\|ref\|>(.*?)<\|/ref\|>"
    r"<\|det\|>\[\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]\]<\|/det\|>"
    r"\n(.*?)(?=<\|ref\|>|\Z)",
    re.DOTALL,
)
_HEADING_RE = re.compile(r"^#{1,6}\s*")
_TABLE_ROW_RE = re.compile(r"^\s*\|.+\|", re.MULTILINE)
_LIST_BULLET_RE = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
_LIST_ORDERED_RE = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
_INLINE_HTML_RE = re.compile(r"<(?:sub|sup)[^>]*>", re.IGNORECASE)

# Matches lines in the LOC format: text followed by 8 <|LOC_N|> tokens encoding
# the four corners of the bounding box: (x0,y0), (x1,y0), (x1,y1), (x0,y1).
_LOC_LINE_RE = re.compile(
    r"^(.*?)"
    r"<\|LOC_(\d+)\|><\|LOC_(\d+)\|><\|LOC_(\d+)\|><\|LOC_(\d+)\|>"
    r"<\|LOC_(\d+)\|><\|LOC_(\d+)\|><\|LOC_(\d+)\|><\|LOC_(\d+)\|>"
    r"\s*$",
    re.MULTILINE,
)


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
                {
                    "type": ref_type,
                    "bbox": (x0, y0, x1, y1),
                    "raw": raw.strip(),
                    "lines": lines,
                }
            )
    return blocks


def _parse_loc_blocks(text: str) -> list[dict]:
    blocks = []
    for m in _LOC_LINE_RE.finditer(text):
        line_text = m.group(1).strip()
        if not line_text:
            continue
        locs = [int(m.group(i)) for i in range(2, 10)]
        x0 = min(locs[0], locs[2], locs[4], locs[6])
        y0 = min(locs[1], locs[3], locs[5], locs[7])
        x1 = max(locs[0], locs[2], locs[4], locs[6])
        y1 = max(locs[1], locs[3], locs[5], locs[7])
        blocks.append(
            {
                "type": "text",
                "bbox": (x0, y0, x1, y1),
                "raw": line_text,
                "lines": [line_text],
            }
        )
    return blocks


def _parse_ocr_text(text: str) -> list[dict]:
    if "<|LOC_" in text:
        return _parse_loc_blocks(text)
    return _parse_ocr_blocks(text)


def _classify_block(block: dict) -> str:
    ref = block["type"].lower()
    if ref == "table":
        return "table"
    if ref in {"list", "list-item"}:
        return "list"
    raw = block.get("raw", "")
    if _TABLE_ROW_RE.search(raw):
        return "table"
    if _LIST_BULLET_RE.search(raw) or _LIST_ORDERED_RE.search(raw):
        return "list"
    return "text"


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _safe_inline_html(text: str) -> str:
    """Escape HTML but preserve <sub>, </sub>, <sup>, </sup> tags."""
    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
    for tag in ("sub", "sup"):
        text = text.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        text = text.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    return text


def _text_line_to_hocr_spans(
    page_number: int,
    line_text: str,
    x0: int,
    ly0: int,
    x1: int,
    ly1: int,
    line_id: int,
    word_id: int,
) -> tuple[list[str], int]:
    result = [
        f'  <span class="ocr_line" id="line_{page_number}_{line_id}" '
        f'title="bbox {x0} {ly0} {x1} {ly1}">'
    ]

    if _INLINE_HTML_RE.search(line_text):
        result.append(
            f'    <span class="ocrx_word" id="word_{page_number}_{word_id}" '
            f'title="bbox {x0} {ly0} {x1} {ly1}">{_safe_inline_html(line_text)}</span>'
        )
        word_id += 1
    else:
        words = line_text.split()
        total_chars = sum(len(w) for w in words) or 1
        line_width = x1 - x0
        wx = x0
        for word in words:
            wx1 = wx + round(line_width * len(word) / total_chars)
            result.append(
                f'    <span class="ocrx_word" id="word_{page_number}_{word_id}" '
                f'title="bbox {wx} {ly0} {wx1} {ly1}">{_escape_html(word)}</span>'
            )
            word_id += 1
            wx = wx1

    result.append("  </span>")
    return result, word_id


def _table_block_to_hocr_lines(
    page_number: int,
    block: dict,
    carea_id: int,
    par_id: int,
    line_id: int,
    word_id: int,
) -> tuple[list[str], int, int]:
    x0, y0, x1, y1 = block["bbox"]
    bbox = f"bbox {x0} {y0} {x1} {y1}"

    table_node = None
    try:
        raw_text = block["raw"]
        if "<table" in raw_text.lower():
            parsed = etree.fromstring(
                f"<div>{raw_text}</div>", etree.HTMLParser()
            )
            table_node = parsed.find(".//table")
        else:
            html_str = md_lib.markdown(raw_text, extensions=["tables"])
            parsed = etree.fromstring(
                f"<div>{html_str}</div>", etree.HTMLParser()
            )
            table_node = parsed.find(".//table")
    except Exception:
        logger.exception(
            "Failed to convert table block to HTML; falling back to plain text "
            "(page=%s, bbox=%s)",
            page_number,
            block.get("bbox"),
        )

    if table_node is None:
        lines_html: list[str] = []
        lines_html.append(
            f'<div class="ocr_carea" id="block_{page_number}_{carea_id}" title="{bbox}">'
        )
        lines_html.append(
            f'<p class="ocr_par" id="par_{page_number}_{par_id}" title="{bbox}">'
        )
        n = len(block["lines"])
        lh = (y1 - y0) / n if n else (y1 - y0)
        for i, line_text in enumerate(block["lines"]):
            ly0_ = round(y0 + i * lh)
            ly1_ = round(y0 + (i + 1) * lh)
            spans, word_id = _text_line_to_hocr_spans(
                page_number, line_text, x0, ly0_, x1, ly1_, line_id, word_id
            )
            lines_html.extend(spans)
            line_id += 1
        lines_html.append("</p>")
        lines_html.append("</div>")
        return lines_html, line_id, word_id

    table_html = etree.tostring(table_node, encoding="unicode")
    result = [
        f'<div class="ocr_carea" id="block_{page_number}_{carea_id}" title="{bbox}">',
        f'<p class="ocr_par" id="par_{page_number}_{par_id}" title="{bbox}">',
        f'  <span class="ocr_line" id="line_{page_number}_{line_id}" title="{bbox}">',
        f"    {table_html}",
        "  </span>",
        "</p>",
        "</div>",
    ]
    return result, line_id + 1, word_id


def _list_block_to_hocr_lines(
    page_number: int,
    block: dict,
    carea_id: int,
    par_id: int,
    line_id: int,
    word_id: int,
) -> tuple[list[str], int, int]:
    x0, y0, x1, y1 = block["bbox"]
    bbox = f"bbox {x0} {y0} {x1} {y1}"

    list_node = None
    try:
        html_str = md_lib.markdown(block["raw"])
        parsed = etree.fromstring(f"<div>{html_str}</div>", etree.HTMLParser())
        list_node = parsed.find(".//ul")
        if list_node is None:
            list_node = parsed.find(".//ol")
    except Exception:
        logger.exception(
            "Failed to convert list block to HTML; falling back to plain text "
            "(page=%s, bbox=%s)",
            page_number,
            block.get("bbox"),
        )

    if list_node is None:
        lines_html: list[str] = []
        lines_html.append(
            f'<div class="ocr_carea" id="block_{page_number}_{carea_id}" title="{bbox}">'
        )
        lines_html.append(
            f'<p class="ocr_par" id="par_{page_number}_{par_id}" title="{bbox}">'
        )
        n = len(block["lines"])
        lh = (y1 - y0) / n if n else (y1 - y0)
        for i, line_text in enumerate(block["lines"]):
            ly0_ = round(y0 + i * lh)
            ly1_ = round(y0 + (i + 1) * lh)
            spans, word_id = _text_line_to_hocr_spans(
                page_number, line_text, x0, ly0_, x1, ly1_, line_id, word_id
            )
            lines_html.extend(spans)
            line_id += 1
        lines_html.append("</p>")
        lines_html.append("</div>")
        return lines_html, line_id, word_id

    list_html = etree.tostring(list_node, encoding="unicode")
    result = [
        f'<div class="ocr_carea" id="block_{page_number}_{carea_id}" title="{bbox}">',
        f'<p class="ocr_par" id="par_{page_number}_{par_id}" title="{bbox}">',
        f'  <span class="ocr_line" id="line_{page_number}_{line_id}" title="{bbox}">',
        f"    {list_html}",
        "  </span>",
        "</p>",
        "</div>",
    ]
    return result, line_id + 1, word_id


def _blocks_to_hocr(
    page_number: int,
    blocks: list[dict],
) -> list[str]:
    hocr: list[str] = []
    carea_id = par_id = line_id = word_id = 1

    for block in blocks:
        kind = _classify_block(block)
        x0, y0, x1, y1 = block["bbox"]

        if kind == "table":
            chunk, line_id, word_id = _table_block_to_hocr_lines(
                page_number, block, carea_id, par_id, line_id, word_id
            )
            hocr.extend(chunk)
            carea_id += 1
            par_id += 1
        elif kind == "list":
            chunk, line_id, word_id = _list_block_to_hocr_lines(
                page_number, block, carea_id, par_id, line_id, word_id
            )
            hocr.extend(chunk)
            carea_id += 1
            par_id += 1
        else:
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
                spans, word_id = _text_line_to_hocr_spans(
                    page_number, line_text, x0, ly0, x1, ly1, line_id, word_id
                )
                hocr.extend(spans)
                line_id += 1

            hocr.append("</p>")
            hocr.append("</div>")

    return hocr


@activity.defn
async def paddle_ocr_results_to_hocr(  # pylint: disable=too-many-locals
    workflow_type: str,
    page_num: int,
    infos: list[dict],
) -> BadgerdocHOCRPageResult:
    """Convert Paddle OCR raw output for one page to hOCR.

    Receives a list of info dicts (one per page-crop or block), each containing:
        middle_json  — MinIO path to the raw OCR output JSON
        metadata     — document metadata (width, height, page, position_in_parent)

    Applies per-block coordinate remapping via metadata.position_in_parent,
    then produces a single hOCR file for the page.
    """
    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
    )

    page_number = page_num

    logger.info(
        "paddle_ocr_results_to_hocr: page %d — %d block(s) to convert",
        page_number,
        len(infos),
    )

    first_page_info = (infos[0].get("metadata") or {}) if infos else {}
    page_width = first_page_info.get("width", 0)
    page_height = first_page_info.get("height", 0)
    display_page_num = first_page_info.get("page") or page_number

    storage_params = storage.StorageWorkflowParams(
        workflow_package="badgerdoc_ocr_paddle",
        workflow_name=workflow_type,
        workflow_id=activity.info().workflow_run_id,
    )

    hocr_lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<title></title>",
        '<meta http-equiv="Content-Type" content="text/html;charset=utf-8">',
        "<meta name='ocr-system' content='paddle-ocr'>",
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
        blocks = _parse_ocr_text(ocr_text)

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

    logger.info(
        "paddle_ocr_results_to_hocr: page %d complete — %d block(s), stored: %s",
        page_number,
        len(all_blocks),
        hocr_path,
    )
    return BadgerdocHOCRPageResult(h_ocr={str(page_number): hocr_path})
