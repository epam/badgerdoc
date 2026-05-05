# Add New OCR Engine

Fully implement and wire a new OCR engine worker for Badgerdoc. This means writing working code for all pipeline methods, not just stubs — research the engine's API, output format, and coordinate system, then implement each `BadgerdocOCRBase` method with real logic.

## What to do

### 1. Create the `uv` package

Create the directory tree under `workflows/`:

```
workflows/
  badgerdoc_ocr_$ARGUMENTS/
    badgerdoc_ocr_$ARGUMENTS/
      __init__.py
      workflow.py
      $ARGUMENTS_ocr.py
      activities/
        __init__.py
        ocr_requests.py
        ocr_convertors.py
    tests/
      __init__.py
    main.py
    pyproject.toml
    Dockerfile
```

`pyproject.toml` must declare `badgerdoc_common` as a local editable path dependency:

```toml
[tool.uv.sources]
badgerdoc_common = { path = "../badgerdoc_common", editable = true }
```

### 2. Implement `BadgerdocOCRBase` in `$ARGUMENTS_ocr.py`

Extend `BadgerdocOCRBase` from `badgerdoc_common.badgerdoc_ocr` and implement all five abstract methods with real working logic. Before writing code, research the engine's Python SDK or HTTP API, its raw output format, and how it represents bounding boxes.

#### `ocr_pages` → `list[BadgerdocOCRPageResult]`

Call the engine on each full-page rendition image. Extract only primitives from `params` before calling `workflow.execute_activity` (see Temporal serialization rule below). Store each result in a `_path_to_context` dict mapping `middle_json_path → (page_num, info_dict)` so `convert_to_hocr` can look up context for every path.

```python
def __init__(self) -> None:
    self._path_to_context: dict[str, tuple[int, dict]] = {}
```

#### `ocr_blocks` → `list[BadgerdocOCRPageResult]`

Same as `ocr_pages` for block crops. Must preserve input order. Insert `BadgerdocOCRPageResult(ocr={})` at the position of any failure. Pass a `block_index` int to the OCR activity so filenames are unique: `page_{N}_block_{I}_middle.json`.

#### `align_coordinates` → `BadgerdocOCRPageResult`

Can be a **pass-through** (`return result`) if coordinate remapping is handled inside `convert_to_hocr`'s convertor activity (which is the recommended pattern — see below).

#### `ocr_merge_blocks` → `list[BadgerdocOCRPageResult]`

Fold block results into page results keyed by page number; one output entry per page:

```python
merged: dict[str, list[str]] = {}
for r in pages + blocks:
    for page_num, paths in r.ocr.items():
        merged.setdefault(page_num, []).extend(paths)
return [BadgerdocOCRPageResult(ocr=merged)]
```

#### `convert_to_hocr` → `list[BadgerdocHOCRPageResult]`

**Group all paths by page number first**, then call the convertor activity **once per page** passing all infos for that page as a list. This ensures multiple blocks on the same page are merged into a single hOCR file keyed by `str(page_num)`.

```python
page_to_infos: dict[int, list[dict]] = {}
for result in results:
    for page_num_str, paths in result.ocr.items():
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

Never produce per-block hOCR keys like `"1_b0"` — the final key must always be `str(page_num)`.

### 3. Design the convertor activity (`ocr_convertors.py`)

The convertor activity signature must accept a **list** of info dicts so it can merge multiple blocks into one page:

```python
@activity.defn
async def your_engine_results_to_hocr(
    workflow_type: str,
    page_num: int,
    infos: list[dict],          # one entry per block/page-crop for this page
) -> BadgerdocHOCRPageResult:
    all_blocks = []
    for info in infos:
        # Download middle_json, parse OCR output into blocks
        ...
        # Apply position_in_parent remapping FOR THIS SPECIFIC INFO
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
        all_blocks.extend(blocks)

    # Generate one hOCR file with all blocks, upload, return single key
    hocr_path = await storage.badgerdoc_store_perm(..., f"page_{page_num}.hocr")
    return BadgerdocHOCRPageResult(h_ocr={str(page_num): hocr_path})
```

Coordinate remapping is **per-info**: each block has its own `metadata.position_in_parent` describing where it sits on the parent page.

### 4. Create `workflow.py`

```python
@workflow.defn
class BadgerdocXxxWorkflow:

    @workflow.run
    async def run(self, params: trigger.DocumentTriggerParams) -> BadgerdocHOCRPageResult:
        ocr_container = await trigger_params_to_ocr_page(params)
        hocr_results = await XxxOCR().run(params, ocr_container)
        combined: dict = {}
        for result in hocr_results:
            combined.update(result.h_ocr)
        return BadgerdocHOCRPageResult(h_ocr=combined)
```

### 5. Register activities in `main.py`

Always include the three `badgerdoc_common` document activities alongside the engine's own activities — they are required by `trigger_params_to_ocr_page`:

```python
from badgerdoc_common.activities.document import (
    badgerdoc_get_document_chunk,
    badgerdoc_get_rendition,
    badgerdoc_list_documents,
)
```

Omitting them causes a `NotFoundError` at runtime.

### 6. Copy and adapt `Dockerfile`

Copy `workflows/badgerdoc_ocr_deepseek_2/Dockerfile` and replace the package name.

### 7. Add service to `docker-compose.yml`

Add a new service block for the worker, setting:
- `build.context` pointing to the new worker directory
- `TEMPORAL_BADGERDOC_ADDRESS`, `BADGERDOC_TOKEN`, `TEMPORAL_ADDRESS` env vars
- `depends_on: [temporal, web]`

### 8. Create a `WorkflowRegistry` fixture or migration

Add a Django fixture (or instruct the user to create a record via admin) with:

| Field | Value |
|---|---|
| `name` | Descriptive name |
| `temporal_workflow_type` | Exact class name from `workflow.py` |
| `temporal_queue` | Must match `task_queue` in `main.py` |
| `trigger` | `manual` |
| `extraction_scope` | `["page"]` or `["page", "block"]` |
| `is_active` | `true` |

### 9. MLX support (if requested)

**Before doing anything**, check whether the requested OCR engine has a published MLX-compatible model on [https://huggingface.co/mlx-community](https://huggingface.co/mlx-community). Search for the engine name in the repository list. If no `mlx-community/<model>` variant exists, inform the user that MLX is not supported for this engine and skip this step entirely.

If an `mlx-community` model is found, append a new `uv run mlx_vlm.server` line to the `start_mlx` target in `Makefile`:

```makefile
start_mlx:
	uv run mlx_vlm.server --port 11434 --model mlx-community/DeepSeek-OCR-2-bf16 & \
	uv run mlx_vlm.server --port 11435 --model mlx-community/PaddleOCR-VL-1.5-bf16 & \
	uv run mlx_vlm.server --port <next_free_port> --model mlx-community/<model-name>
```

Choose the next free port by incrementing from the highest port already used in `start_mlx`. Tell the user which port was assigned so they can configure the worker to point at it.

## Rules

- All pipeline steps **must** emit `logger.info` log lines at the start and completion of each method, including the number of pages/blocks being processed and any notable intermediate outcomes (e.g. pages skipped, blocks failed, coordinates shifted). Upstream infrastructure reads worker logs and surfaces them to the user in the UI, so logs are the primary progress and status signal — treat them as user-facing messages, not internal debug noise.
- Any environment variables introduced by the new worker (API keys, model endpoints, inference timeouts, MLX server URLs, etc.) **must** be added to `.env_example` at the project root with a placeholder value and a short inline comment explaining what the variable controls. This is the canonical reference for required configuration — do not leave env vars undocumented.
- All I/O inside the workflow (including calls inside `BadgerdocOCRBase`) **must** go through `workflow.execute_activity()` with `start_to_close_timeout` and `retry_policy` from `badgerdoc_common.helpers`. Never call `@activity.defn` functions directly from workflow code.
- Use `helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT` and `helpers.BadgerdocRestAPIRetryPolicy` for any REST activity calls.
- `ocr_blocks` must preserve the exact input order. Use `asyncio.gather` for concurrent fetching when possible.
- The hOCR output produced by `convert_to_hocr` **must** conform to the spec in `web/docs/docs/extraction_formats.md`. Key constraints:
  - All bounding-box coordinates (`bbox`) must be integers in the range `[0, 1000]`.
  - Root-level content blocks must use the class `ocr_carea`.
  - Required capabilities: `ocr_photo`, `ocr_page`, `ocr_carea`, `ocr_par`, `ocr_line`, `ocrx_word`.
  - Page IDs follow the pattern `page_<page_number>` (1-based).
  - All other element IDs follow the pattern `<tag_name>_<page_number>_<tag_index>` (e.g. `block_4_5`).
- See `web/docs/docs/badgerdoc_ocr.md` for the full pipeline description and coordinate alignment details.

## Temporal serialization — critical constraint

**Temporal's default JSON converter does NOT reconstruct Python `@dataclass` instances from activity arguments.** It deserializes JSON objects as plain `dict`, even when the parameter has a dataclass type hint. This applies to ALL dataclass args passed via `workflow.execute_activity(..., args=[...])`.

**Two rules that must always hold:**

1. **In `XxxOCR` (the `BadgerdocOCRBase` subclass):** Only pass primitives (`int`, `str`, `list[str]`, `dict`) or flat dataclasses whose fields are all primitives (like `BadgerdocDocument`) as `args` to `workflow.execute_activity`. Extract values from nested objects at the call site:

   ```python
   # WRONG — DocumentTriggerParams contains nested dataclasses
   args=[params, req.badgerdoc_document]

   # CORRECT — extract primitives before the call
   args=[params.target_extraction.id, params.target_extraction.tags or [],
         params.workflow.temporal_workflow_type,
         req.badgerdoc_document.page_num,
         req.badgerdoc_document.document]   # BadgerdocDocument is flat → OK
   ```

2. **In every `@activity.defn` that receives a dataclass argument:** Add a defensive reconstruction guard at the top of the function body:

   ```python
   @activity.defn
   async def my_activity(doc: BadgerdocDocument, ...) -> ...:
       if isinstance(doc, dict):
           doc = BadgerdocDocument(**doc)
       ...
   ```

   Apply the same pattern to every `badgerdoc_common` activity that receives a dataclass (`badgerdoc_get_rendition`, `badgerdoc_list_documents`, `badgerdoc_get_document_chunk`, etc.) — they are already patched in the codebase, but any new activity must follow the same rule.

**Why `DocumentTriggerParams` works at the workflow level but not activity level:** Temporal correctly reconstructs dataclasses from the workflow `run` method's input (top-level workflow argument), so `params: DocumentTriggerParams` in `workflow.run` is always a proper dataclass. The failure is specific to arguments passed through `workflow.execute_activity(..., args=[...])`.
