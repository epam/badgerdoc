# hOCR Output Specification

## Bounding box constraints

All bounding-box coordinates (`bbox`) must be **integers in the range `[0, 1000]`**, normalized to the page dimensions. Never emit float coordinates; always `round()` before casting to `int`.

## Required capabilities

The hOCR document must declare all six capabilities in the `<meta>` header:

```
ocr_photo, ocr_page, ocr_carea, ocr_par, ocr_line, ocrx_word
```

## Element class requirements

- Root-level content blocks must use the class `ocr_carea`.
- Hierarchy: `ocr_page` → `ocr_carea` → `ocr_par` → `ocr_line` → `ocrx_word`

## ID patterns

- Page element: `page_<page_number>` (1-based, e.g. `page_1`, `page_2`)
- All other elements: `<tag_name>_<page_number>_<tag_index>` (e.g. `block_4_5`, `line_1_3`)

## Page key convention

The final hOCR result dict key must **always** be `str(page_num)`. Never produce per-block suffixes like `"1_b0"`. When merging multiple blocks for the same page, all blocks go into one hOCR file under a single `str(page_num)` key.

## Convertor activity merge pattern

Group all paths by page number first, then call the convertor activity **once per page** passing all infos for that page as a list:

```python
page_to_infos: dict[int, list[dict]] = {}
for result in results:
    for _, paths in result.ocr.items():
        for path in paths:
            page_num, info = self._path_to_context[path]
            page_to_infos.setdefault(page_num, []).append(info)

for page_num, infos in page_to_infos.items():
    hocr_result = await workflow.execute_activity(
        your_results_to_hocr,
        args=[workflow_type, page_num, infos],
        ...
    )
```

## Convertor activity signature

The convertor activity must accept a **list** of info dicts so it can merge multiple blocks into one page:

```python
@activity.defn
async def your_engine_results_to_hocr(
    workflow_type: str,
    page_num: int,
    infos: list[dict],   # one entry per block/page-crop for this page
) -> BadgerdocHOCRPageResult:
    ...
    return BadgerdocHOCRPageResult(h_ocr={str(page_num): hocr_path})
```

## Coordinate remapping

Coordinate remapping is **per-info**: each block has its own `metadata.position_in_parent` describing where it sits on the parent page. Apply remapping inside the convertor activity, after downloading the middle JSON for each info:

```python
position_in_parent = (info.get("metadata") or {}).get("position_in_parent")
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
```

See `web/docs/docs/extraction_formats.md` for the full hOCR format reference.
