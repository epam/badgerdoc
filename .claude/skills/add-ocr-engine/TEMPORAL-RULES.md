# Temporal Serialization Rules

## Serialization constraint

Temporal's default JSON converter does NOT reconstruct Python `@dataclass` instances from activity arguments. It deserializes JSON objects as plain `dict`, even when the parameter has a dataclass type hint. This applies to ALL dataclass args passed via `workflow.execute_activity(..., args=[...])`.

## Rule 1: Extract primitives before calling `workflow.execute_activity`

In the `BadgerdocOCRBase` subclass, only pass primitives (`int`, `str`, `list[str]`, `dict`) or flat dataclasses whose fields are all primitives (like `BadgerdocDocument`) as `args` to `workflow.execute_activity`. Extract values from nested objects at the call site.

```python
# WRONG — DocumentTriggerParams contains nested dataclasses
args=[params, req.badgerdoc_document]

# CORRECT — extract primitives before the call
args=[params.target_extraction.id, params.target_extraction.tags or [],
      params.workflow.temporal_workflow_type,
      req.badgerdoc_document.page_num,
      req.badgerdoc_document.document]   # BadgerdocDocument is flat → OK
```

## Rule 2: Defensive reconstruction guard in every `@activity.defn`

Add a defensive reconstruction guard at the top of every activity that receives a dataclass argument:

```python
@activity.defn
async def my_activity(doc: BadgerdocDocument, ...) -> ...:
    if isinstance(doc, dict):
        doc = BadgerdocDocument(**doc)
    ...
```

Apply the same pattern to every `badgerdoc_common` activity that receives a dataclass — they are already patched in the codebase, but any new activity must follow the same rule.

## Rule 3: All I/O must go through `workflow.execute_activity`

All I/O inside the workflow (including calls inside `BadgerdocOCRBase`) **must** go through `workflow.execute_activity()` with `start_to_close_timeout` and `retry_policy` from `badgerdoc_common.helpers`. Never call `@activity.defn` functions directly from workflow code.

## Timeout and retry policy constants

Use these for REST API activities:

- `helpers.BADGERDOC_REST_API_START_TO_CLOSE_TIMEOUT`
- `helpers.BadgerdocRestAPIRetryPolicy`

## Why `DocumentTriggerParams` works at the workflow level but not activity level

Temporal correctly reconstructs dataclasses from the workflow `run` method's input (top-level workflow argument), so `params: DocumentTriggerParams` in `workflow.run` is always a proper dataclass. The failure is specific to arguments passed through `workflow.execute_activity(..., args=[...])`.
