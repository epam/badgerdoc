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
_LIST_BULLET_RE = re.compile(r"^\s*[-*+\u2022]\s+", re.MULTILINE)
_LIST_ORDERED_RE = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
_INLINE_HTML_RE = re.compile(r"<(?:sub|sup)[^>]*>", re.IGNORECASE)


# This module converts entities like tables, lists, and sub/superscripts
# in the OCR text into structured HOCR output:
# - Tables: When a block has ref_type="table" or its content matches a
#   | ... | row pattern, markdown.markdown(..., extensions=["tables"])
#   converts the GFM table to HTML and the <table> element is embedded
#   inside a single ocr_line span.
# - Lists: Same approach — bullet/ordered lists are converted via
#   markdown.markdown(), the <ul>/<ol> node is extracted with lxml and
#   embedded in ocr_line.
# - Sub-/superscripts: Plain text lines containing <sub> or <sup> are
#   emitted as a single ocrx_word using _safe_inline_html(), which
#   escapes everything except those two tags. All other text lines
#   retain the existing per-word proportional bbox splitting.


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


def _classify_block(block: dict) -> str:
    ref = block["type"].lower()
    if ref == "table":
        return "table"
    if ref in {"list", "list-item"}:
        return "list"
    raw = block.get("raw", "")
    if _TABLE_ROW_RE.search(raw):
        return "table"
    # Check if any line starts with a list marker
    lines = block.get("lines", [])
    for line in lines:
        if _LIST_BULLET_RE.match(line) or _LIST_ORDERED_RE.match(line):
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
    """Render one plain-text line as ocr_line > ocrx_word spans.

    Lines containing <sub>/<sup> tags are emitted as a single ocrx_word
    to preserve the inline HTML without word splitting.
    """
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


# Update _list_block_to_hocr_lines to render each list item as a separate line
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

    lines = block["lines"]
    hocr: list[str] = []

    hocr.append(
        f'<div class="ocr_carea" id="block_{page_number}_{carea_id}" title="{bbox}">'
    )
    hocr.append(
        f'<p class="ocr_par" id="par_{page_number}_{par_id}" title="{bbox}">'
    )

    n_lines = len(lines)
    line_height = (y1 - y0) / n_lines if n_lines else (y1 - y0)

    for i, line_text in enumerate(lines):
        # Remove list markers (-, *, +, •, or numbered)
        clean_line = _LIST_BULLET_RE.sub("", line_text)
        clean_line = _LIST_ORDERED_RE.sub("", clean_line).strip()

        ly0 = round(y0 + i * line_height)
        ly1 = round(y0 + (i + 1) * line_height)

        spans, word_id = _text_line_to_hocr_spans(
            page_number, clean_line, x0, ly0, x1, ly1, line_id, word_id
        )
        hocr.extend(spans)
        line_id += 1

    hocr.append("</p>")
    hocr.append("</div>")

    return hocr, line_id, word_id


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
async def deepseek_ocr_2_results_to_hocr(  # pylint: disable=too-many-locals
    workflow_type: str,
    page_num: int,
    infos: list[dict],
) -> BadgerdocHOCRPageResult:
    """Convert DeepSeek OCR raw output for one page to hOCR.

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
        "deepseek_ocr_2_results_to_hocr: page %d — %d block(s) to convert",
        page_number,
        len(infos),
    )

    first_page_info = (infos[0].get("metadata") or {}) if infos else {}
    size = first_page_info.get("size") or {}
    page_width = size.get("width") or first_page_info.get("width") or 1000
    page_height = size.get("height") or first_page_info.get("height") or 1000
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
    logger.info(
        "deepseek_ocr_2_results_to_hocr: page %d complete — %d block(s), stored: %s",
        page_number,
        len(all_blocks),
        hocr_path,
    )
    return BadgerdocHOCRPageResult(h_ocr={str(page_number): hocr_path})
