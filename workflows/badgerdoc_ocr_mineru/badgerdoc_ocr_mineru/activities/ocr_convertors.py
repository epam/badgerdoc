import json
import logging
import re
from io import BytesIO

from temporalio import activity

from badgerdoc_common.hocr import BadgerdocHOCRPageResult

logger = logging.getLogger(__name__)

_HEADING_RE = re.compile(r"^#{1,6}\s+")
_TABLE_ROW_RE = re.compile(r"^\s*\|")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
_FCEL_TABLE_RE = re.compile(r"<(?:fcel|lcel|ucel)>")


def _parse_markdown_blocks(text: str) -> list[dict]:
    """Parse markdown text into semantic blocks (text/title/table/list)."""
    blocks: list[dict] = []
    current_type = "text"
    current_lines: list[str] = []

    def flush() -> None:
        content = [ln for ln in current_lines if ln.strip()]
        if content:
            blocks.append({"type": current_type, "lines": content})

    for raw in text.splitlines():
        if _HEADING_RE.match(raw):
            flush()
            current_lines = []
            heading_text = _HEADING_RE.sub("", raw).strip()
            if heading_text:
                blocks.append({"type": "title", "lines": [heading_text]})
            current_type = "text"
            continue

        if _FCEL_TABLE_RE.search(raw):
            if current_type != "fcel_table":
                flush()
                current_lines = []
                current_type = "fcel_table"
            current_lines.append(raw)
            continue

        if _TABLE_ROW_RE.match(raw):
            if current_type != "table":
                flush()
                current_lines = []
                current_type = "table"
            current_lines.append(raw)
            continue

        if _LIST_ITEM_RE.match(raw):
            if current_type != "list":
                flush()
                current_lines = []
                current_type = "list"
            current_lines.append(raw)
            continue

        if not raw.strip():
            flush()
            current_lines = []
            current_type = "text"
            continue

        if current_type not in ("text",):
            flush()
            current_lines = []
            current_type = "text"
        current_lines.append(raw)

    flush()
    return blocks


def _assign_proportional_bboxes(blocks: list[dict]) -> list[dict]:
    """Distribute blocks vertically (0–1000) proportional to line count."""
    if not blocks:
        return []
    total = sum(len(b["lines"]) for b in blocks) or 1
    y = 0
    result = []
    for b in blocks:
        n = len(b["lines"])
        h = max(int(n / total * 1000), 10)
        h = min(h, 1000 - y)
        result.append({**b, "bbox": (0, y, 1000, y + h)})
        y += h
    return result


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _fcel_table_to_html(lines: list[str]) -> str:
    """Convert MinerU <fcel>/<lcel>/<ucel>/<nl> table format to an HTML table string.

    <fcel> — normal cell
    <lcel> — merge with the cell to the left (extends its colspan)
    <ucel> — merge with the cell above (extends its rowspan)
    """
    raw = " ".join(lines)
    row_texts = [r for r in raw.split("<nl>") if r.strip()]
    if not row_texts:
        return "<table></table>"

    # Parse each row into (cell_type, content) pairs
    _CELL_TOKEN_RE = re.compile(r"(<fcel>|<lcel>|<ucel>)")
    grid: list[list[dict]] = []
    for row_text in row_texts:
        row: list[dict] = []
        parts = _CELL_TOKEN_RE.split(row_text)
        cell_type: str | None = None
        for part in parts:
            if part in ("<fcel>", "<lcel>", "<ucel>"):
                cell_type = part[1:-1]
            elif cell_type is not None:
                row.append(
                    {
                        "type": cell_type,
                        "content": part.strip(),
                        "colspan": 1,
                        "rowspan": 1,
                        "skip": False,
                    }
                )
                cell_type = None
        if cell_type is not None:
            row.append(
                {
                    "type": cell_type,
                    "content": "",
                    "colspan": 1,
                    "rowspan": 1,
                    "skip": False,
                }
            )
        if row:
            grid.append(row)

    if not grid:
        return "<table></table>"

    # owner[r][c] = (anchor_r, anchor_c) — the top-left cell that owns this position
    owner: list[list[tuple[int, int]]] = [
        [(r, c) for c in range(len(row))] for r, row in enumerate(grid)
    ]

    # Resolve <lcel>: extend colspan of the anchor to the left (left → right pass)
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell["type"] == "lcel" and c > 0:
                anchor = owner[r][c - 1]
                owner[r][c] = anchor
                ar, ac = anchor
                grid[ar][ac]["colspan"] += 1
                cell["skip"] = True

    # Resolve <ucel>: extend rowspan of the anchor above (top → bottom pass).
    # Track rows already claimed per anchor to avoid double-counting in merged regions.
    claimed_rows: dict[tuple[int, int], set[int]] = {}
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell["type"] == "ucel" and r > 0:
                above_row = grid[r - 1]
                if c >= len(above_row):
                    continue
                anchor = owner[r - 1][c]
                owner[r][c] = anchor
                cell["skip"] = True
                ar, ac = anchor
                if (ar, ac) not in claimed_rows:
                    claimed_rows[(ar, ac)] = set()
                if r not in claimed_rows[(ar, ac)]:
                    claimed_rows[(ar, ac)].add(r)
                    grid[ar][ac]["rowspan"] += 1

    # Render HTML
    html_rows: list[str] = []
    for r, row in enumerate(grid):
        tag = "th" if r == 0 else "td"
        cells_html = ""
        for cell in row:
            if cell["skip"]:
                continue
            attrs = ""
            if cell["colspan"] > 1:
                attrs += f' colspan="{cell["colspan"]}"'
            if cell["rowspan"] > 1:
                attrs += f' rowspan="{cell["rowspan"]}"'
            cells_html += (
                f"<{tag}{attrs}>{_escape_html(cell['content'])}</{tag}>"
            )
        if cells_html:
            html_rows.append(f"<tr>{cells_html}</tr>")

    if not html_rows:
        return "<table></table>"

    thead = f"<thead>{html_rows[0]}</thead>"
    tbody = (
        f"<tbody>{''.join(html_rows[1:])}</tbody>"
        if len(html_rows) > 1
        else ""
    )
    return f"<table>{thead}{tbody}</table>"


def _parse_mineru_blocks(raw_blocks: list[dict]) -> list[dict]:
    """Convert mineru-vl-utils ContentBlock list to internal hOCR-ready format.

    Bboxes from mineru-vl-utils are normalized [0, 1]; we scale them to [0, 1000]
    to match the hOCR coordinate space used throughout this module.
    """
    result: list[dict] = []
    for b in raw_blocks:
        content: str = b.get("content") or ""
        bbox_norm: list[float] = b.get("bbox") or [0.0, 0.0, 1.0, 1.0]
        btype: str = b.get("type") or "text"

        x0 = round(bbox_norm[0] * 1000)
        y0 = round(bbox_norm[1] * 1000)
        x1 = round(bbox_norm[2] * 1000)
        y1 = round(bbox_norm[3] * 1000)

        if btype == "title":
            internal_type = "title"
            lines = [content.strip()] if content.strip() else []
        elif btype == "table":
            if "<table" in content.lower():
                internal_type = "html_table"
            elif _FCEL_TABLE_RE.search(content):
                internal_type = "fcel_table"
            else:
                internal_type = "text"
            lines = [content] if content.strip() else []
        else:
            internal_type = "text"
            lines = [ln for ln in content.splitlines() if ln.strip()]

        if lines:
            result.append(
                {
                    "type": internal_type,
                    "lines": lines,
                    "bbox": (x0, y0, x1, y1),
                }
            )
    return result


def _table_block_to_hocr_lines(
    page_number: int,
    block: dict,
    carea_id: int,
    par_id: int,
    line_id: int,
) -> list[str]:
    x0, y0, x1, y1 = block["bbox"]
    bbox = f"bbox {x0} {y0} {x1} {y1}"
    if block["type"] == "html_table":
        table_html = block["lines"][0]
    else:
        table_html = _fcel_table_to_html(block["lines"])
    return [
        f'<div class="ocr_carea" id="block_{page_number}_{carea_id}" title="{bbox}">',
        f'<p class="ocr_par" id="par_{page_number}_{par_id}" title="{bbox}">',
        f'  <span class="ocr_line" id="line_{page_number}_{line_id}" title="{bbox}">',
        f"    {table_html}",
        "  </span>",
        "</p>",
        "</div>",
    ]


def _blocks_to_hocr_lines(page_number: int, blocks: list[dict]) -> list[str]:
    lines: list[str] = []
    carea_id = par_id = line_id = word_id = 1

    for block in blocks:
        if block["type"] in ("fcel_table", "html_table"):
            chunk = _table_block_to_hocr_lines(
                page_number, block, carea_id, par_id, line_id
            )
            lines.extend(chunk)
            carea_id += 1
            par_id += 1
            line_id += 1
            continue

        x0, y0, x1, y1 = block["bbox"]
        bbox_str = f"bbox {x0} {y0} {x1} {y1}"
        block_lines = block["lines"]
        n = len(block_lines)
        lh = (y1 - y0) / n if n else (y1 - y0)

        lines.append(
            f'<div class="ocr_carea" id="block_{page_number}_{carea_id}" title="{bbox_str}">'
        )
        carea_id += 1

        par_class = "ocr_header" if block["type"] == "title" else "ocr_par"
        lines.append(
            f'<p class="{par_class}" id="par_{page_number}_{par_id}" title="{bbox_str}">'
        )
        par_id += 1

        for i, line_text in enumerate(block_lines):
            ly0 = round(y0 + i * lh)
            ly1 = round(y0 + (i + 1) * lh)
            lines.append(
                f'<span class="ocr_line" id="line_{page_number}_{line_id}" '
                f'title="bbox {x0} {ly0} {x1} {ly1}">'
            )
            line_id += 1

            # Each token is a word + its original trailing whitespace
            tokens = re.findall(r"\S+\s*", line_text)
            total_chars = sum(len(t.rstrip()) for t in tokens) or 1
            line_width = x1 - x0
            wx = x0
            for token in tokens:
                word = token.rstrip()
                wx1 = wx + round(line_width * len(word) / total_chars)
                lines.append(
                    f'<span class="ocrx_word" id="word_{page_number}_{word_id}" '
                    f'title="bbox {wx} {ly0} {wx1} {ly1}">{_escape_html(token)}</span>'
                )
                word_id += 1
                wx = wx1

            lines.append("</span>")

        lines.append("</p>")
        lines.append("</div>")

    return lines


@activity.defn
async def mineru_mlx_results_to_hocr(
    workflow_type: str,
    page_num: int,
    page_manifest_path: str,
) -> BadgerdocHOCRPageResult:
    """Convert MinerU MLX raw output for one page to hOCR.

    Reads the per-page manifest from MinIO (a list of info dicts produced by
    mineru_mlx_merge_and_store for this specific page), then converts all
    blocks into a single hOCR file with per-block coordinate remapping via
    metadata.position_in_parent.
    """
    from badgerdoc_common import (  # pylint: disable=import-outside-toplevel
        storage,
    )

    manifest_buffer = BytesIO()
    await storage.badgerdoc_download(manifest_buffer, page_manifest_path)
    manifest_buffer.seek(0)
    infos: list[dict] = json.load(manifest_buffer)

    logger.info(
        "mineru_mlx_results_to_hocr: page %d — %d block(s) to convert",
        page_num,
        len(infos),
    )

    storage_params = storage.StorageWorkflowParams(
        workflow_package="badgerdoc_ocr_mineru",
        workflow_name=workflow_type,
        workflow_id=activity.info().workflow_run_id,
    )

    all_blocks: list[dict] = []
    for info in infos:
        middle_json_path = info.get("middle_json")
        if not middle_json_path:
            logger.warning(
                "mineru_mlx_results_to_hocr: page %d — missing middle_json, skipping",
                page_num,
            )
            continue

        buf = BytesIO()
        await storage.badgerdoc_download(buf, middle_json_path)
        buf.seek(0)
        data = json.load(buf)

        if "blocks" in data:
            blocks = _parse_mineru_blocks(data["blocks"])
        else:
            # Legacy fallback: old single-prompt markdown format
            blocks = _parse_markdown_blocks(data.get("text", ""))
            blocks = _assign_proportional_bboxes(blocks)

        position_in_parent: str | None = (info.get("metadata") or {}).get(
            "position_in_parent"
        )
        if position_in_parent:
            cx1, cy1, cx2, cy2 = map(int, position_in_parent.split())
            cw, ch = cx2 - cx1, cy2 - cy1
            for block in blocks:
                bx1, by1, bx2, by2 = block["bbox"]
                block["bbox"] = (
                    cx1 + round(bx1 * cw / 1000),
                    cy1 + round(by1 * ch / 1000),
                    cx1 + round(bx2 * cw / 1000),
                    cy1 + round(by2 * ch / 1000),
                )
            logger.info(
                "mineru_mlx_results_to_hocr: page %d — applied position_in_parent remapping",
                page_num,
            )

        all_blocks.extend(blocks)

    first_meta = (infos[0].get("metadata") or {}) if infos else {}
    display_page_num = first_meta.get("page") or page_num

    hocr_lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<title></title>",
        '<meta http-equiv="Content-Type" content="text/html;charset=utf-8">',
        "<meta name='ocr-system' content='mineru-mlx'>",
        "<meta name='ocr-capabilities' content='ocr_photo ocr_page ocr_carea ocr_par ocr_line ocrx_word'>",
        "</head>",
        "<body>",
        f'<div class="ocr_page" id="page_{display_page_num}" '
        f'title="bbox 0 0 1000 1000; ppageno {display_page_num}">',
    ]
    hocr_lines.extend(_blocks_to_hocr_lines(page_num, all_blocks))
    hocr_lines.extend(["</div>", "</body>", "</html>"])

    hocr_content = "\n".join(hocr_lines)
    hocr_path = await storage.badgerdoc_store_perm(
        BytesIO(hocr_content.encode("utf-8")),
        storage_params,
        f"page_{page_num}.hocr",
    )
    logger.info(
        "mineru_mlx_results_to_hocr: page %d complete — %d block(s), stored: %s",
        page_num,
        len(all_blocks),
        hocr_path,
    )
    return BadgerdocHOCRPageResult(h_ocr={str(page_num): hocr_path})
