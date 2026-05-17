# Integration Checklist

Use this checklist as a validation guard after creating the task list. Every item must have a corresponding task before implementation begins.

## Structural integration steps

- [ ] **Package scaffolding** — `workflows/badgerdoc_ocr_<tag>/` directory tree created with `pyproject.toml` declaring `badgerdoc_common` as a local editable dependency
- [ ] **`BadgerdocOCRBase` subclass** — `<tag>_ocr.py` extends `BadgerdocOCRBase` and implements all five abstract methods (`ocr_pages`, `ocr_blocks`, `align_coordinates`, `ocr_merge_blocks`, `convert_to_hocr`) with real working logic
- [ ] **Convertor activity** — `ocr_convertors.py` contains the `@activity.defn` convertor function that accepts `list[dict]` infos and returns `BadgerdocHOCRPageResult` with a single `str(page_num)` key
- [ ] **Workflow** — `workflow.py` defines the `@workflow.defn` class; `workflow.run()` only calls `trigger_params_to_ocr_page` and delegates to `EngineOCR().run()`
- [ ] **`main.py`** — registers the engine's own activities plus the three `badgerdoc_common` document activities (`badgerdoc_get_document_chunk`, `badgerdoc_get_rendition`, `badgerdoc_list_documents`) and the extraction-tagging activity
- [ ] **Dockerfile** — copied and adapted from an existing OCR worker (e.g. `badgerdoc_ocr_deepseek_2`), package name replaced
- [ ] **`docker-compose.yml` service** — new service block added with `TEMPORAL_BADGERDOC_ADDRESS`, `BADGERDOC_TOKEN`, `TEMPORAL_ADDRESS` env vars and `depends_on: [temporal, web]`
- [ ] **`WorkflowRegistry` entry** — entry added to `web/badgerdoc/fixtures/workflowregistry.json` (not just documented in README) with `temporal_workflow_type`, `temporal_queue` (must match `task_queue` in `main.py`), `trigger`, `extraction_scope`, and `is_active: true`
- [ ] **`Tag` fixture entry** — entry added to `web/badgerdoc/fixtures/tags.json` with `tag` (kebab-case slug matching the tag used in the `WorkflowRegistry` `tags` array), `literal` (human-readable display name), and `order` (next available integer); this persists the tag for fresh setups since `useTags()` caches with `staleTime: Infinity`
- [ ] **Env vars in `.env_example`** — every new env var introduced by the worker documented with a placeholder value and inline comment
- [ ] **MLX support** *(conditional — only if an `mlx-community/<model>` variant exists on HuggingFace)* — `start_mlx` target in `Makefile` updated with a new `uv run mlx_vlm.server` line at the next free port
