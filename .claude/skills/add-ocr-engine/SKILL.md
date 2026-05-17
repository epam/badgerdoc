---
description: Implement and wire a new OCR engine worker into Badgerdoc
context: fork
effort: high
disable-model-invocation: true
arguments: ocr-tag path-to-ocr-repository
---

# Add OCR Engine

This skill integrates a new OCR engine into the Badgerdoc pipeline. It runs in four phases: **Explore → Gate → Tasks → Implement**. Each phase hands off to the next via a persistent artifact on disk; if context is lost, resume by reading the manifest and calling TaskList.

---

## Phase 1: Exploration

Spawn a **single** exploration subagent with the briefing below. Do not split into two parallel subagents — the subagent must reconcile engine API knowledge with codebase hOCR expectations in one pass so the Integration Delta already accounts for format mismatches. See `docs/adr/0001-single-exploration-subagent.md` for the rationale.

**Before spawning**, substitute all placeholders in the briefing:
- Replace every `<ocr-tag>` with the actual `ocr-tag` argument value.
- Replace every `<repo-root>` with the output of `git rev-parse --show-toplevel`.
- Resolve the `<if>` / `</if>` conditionals: keep only the block that matches whether `path-to-ocr-repository` was provided; remove the other block and the `<if>` tags entirely.
Pass the fully substituted text to the subagent — never pass the template with placeholders intact.

### Subagent briefing template

```
You are researching a new OCR engine for integration into Badgerdoc.

## Your two tasks (complete both in one pass)

### Task 1: Engine API research
<if path-to-ocr-repository was provided>
Primary source: read the repository at <path-to-ocr-repository>.
Learn: how to authenticate, how to invoke inference (SDK call or HTTP endpoint),
what the raw output looks like (JSON shape, bbox format, coordinate space).
Fall back to web search only for gaps the repo does not answer.
</if>
<if no path-to-ocr-repository>
Search the web for the engine's Python SDK or HTTP API documentation.
Learn: authentication, invocation, raw output shape, coordinate space.
</if>

### Task 2: Codebase analysis
Examine the existing OCR workers in `workflows/badgerdoc_ocr_*/` to understand:
- The `BadgerdocOCRBase` interface (five abstract methods) in `badgerdoc_common`
- How an existing worker (e.g. deepseek_2) implements each method
- What files every worker must contain (package layout, Dockerfile, main.py pattern)
- How coordinates are normalized to the [0, 1000] hOCR range

## Output

First create the output directory:
```bash
mkdir -p <repo-root>/local/ocr-integration/<ocr-tag>
```
Then write your findings to `<repo-root>/local/ocr-integration/<ocr-tag>/manifest.md` with exactly
these four sections:

### Engine API Summary
Authentication method, invocation pattern, raw output JSON shape, coordinate space.

### Integration Delta
A checklist of specific files and modules to create or modify, with one line of
context for each item explaining what it must do. This is the source of truth
for task creation — be precise.

### Coordinate Mapping
How engine bboxes map to the [0, 1000] hOCR range. If already normalized, write
"pass-through". Otherwise describe the formula.

### Open Questions
Anything you could not resolve with confidence. If none, write "None".
```

After the subagent completes, run this check before proceeding:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel) && \
test -f "$REPO_ROOT/local/ocr-integration/<ocr-tag>/manifest.md" && echo "MANIFEST OK" || echo "MANIFEST MISSING"
```

If the output is `MANIFEST MISSING`, do not proceed — instruct the subagent to write the manifest to `$REPO_ROOT/local/ocr-integration/<ocr-tag>/manifest.md` and re-run the check until it passes.

---

## Phase 2: Open Question Gate

Run `git rev-parse --show-toplevel` to get the repo root, then read `<repo-root>/local/ocr-integration/<ocr-tag>/manifest.md` from disk.

Locate the **Open Questions** section.

- If it contains only "None" or is otherwise empty: proceed immediately to Phase 3 — no user prompt needed.
- If it contains one or more questions: present each question to the user clearly, numbered, and wait for answers before proceeding. Then update the manifest's Open Questions section with the resolved answers (overwrite the question lines with "Resolved: <answer>").

Do not create any tasks until all open questions are resolved.

---

## Phase 3: Task Creation

Run `git rev-parse --show-toplevel` to get the repo root, then read `<repo-root>/local/ocr-integration/<ocr-tag>/manifest.md` from disk. Use the **Integration Delta** section as the source of tasks — do not use a fixed template.

For each item in the Integration Delta, call `TaskCreate` with:
- **subject**: what to build (one line, imperative)
- **description**: the item's context line from the delta plus a "Load before starting:" instruction naming the relevant reference file(s):
  - For any task involving activity or workflow code: "Load before starting: run `git rev-parse --show-toplevel` and read `<repo-root>/.claude/skills/add-ocr-engine/TEMPORAL-RULES.md`"
  - For any task involving the convertor activity or `convert_to_hocr`: "Load before starting: run `git rev-parse --show-toplevel` and read `<repo-root>/.claude/skills/add-ocr-engine/HOCR-SPEC.md`"
  - For scaffolding, Dockerfile, docker-compose, WorkflowRegistry, env vars: no reference file needed

Set `addBlockedBy` relationships so tasks are worked in dependency order (e.g. the convertor task blocks the workflow task; the workflow task blocks `main.py`).

After all tasks are created, run `git rev-parse --show-toplevel` and read `<repo-root>/.claude/skills/add-ocr-engine/INTEGRATION-CHECKLIST.md`. Verify that every checklist item has a corresponding task. Create any missing tasks using the same pattern above. This is a validation pass, not the source of task definitions.

---

## Phase 4: Implementation

Work through tasks in kanban order (lowest unblocked task first). For each task:

1. Call `TaskUpdate` to set the task to `in_progress`.
2. Read the task description — it is self-contained. Work from it plus the reference file it names. Do not re-read the full manifest or SKILL.md for each task.
3. **Rule loading triggers** — run `git rev-parse --show-toplevel` once to get `<repo-root>`, then read the named file at the moment you start the relevant task, not before:
   - Read `<repo-root>/.claude/skills/add-ocr-engine/TEMPORAL-RULES.md` before writing any `@activity.defn` function or any `workflow.execute_activity` call.
   - Read `<repo-root>/.claude/skills/add-ocr-engine/HOCR-SPEC.md` before implementing the convertor activity or any `convert_to_hocr` method.
   - `INTEGRATION-CHECKLIST.md` was already loaded during Phase 3 and does not need to be re-read per task.
4. Complete the task, then call `TaskUpdate` to set it to `completed`.
5. Move to the next unblocked task.

### Context recovery

If context is lost mid-implementation:
1. Run `git rev-parse --show-toplevel` and read `<repo-root>/local/ocr-integration/<ocr-tag>/manifest.md` to restore understanding of the integration.
2. Call `TaskList` to find which tasks are complete, in-progress, and pending.
3. Resume from the next incomplete task, loading its description and the reference file it names.

### Completion gate

After all tasks are marked `completed`, run the following checks. Every command must print `OK`. If any prints a failure, create and complete the missing task before declaring the integration done.

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
OCR_TAG=<ocr-tag>
WORKFLOW_CLASS="Badgerdoc$(python3 -c "print(''.join(w.capitalize() for w in '$OCR_TAG'.split('_')))")Workflow"

# 1. WorkflowRegistry fixture entry exists
grep -q "\"temporal_workflow_type\": \"$WORKFLOW_CLASS\"" \
  "$REPO_ROOT/web/badgerdoc/fixtures/workflowregistry.json" \
  && echo "FIXTURE OK" || echo "FIXTURE MISSING: $WORKFLOW_CLASS not in workflowregistry.json"

# 2. task_queue in main.py matches temporal_queue in fixture
QUEUE=$(grep 'task_queue' "$REPO_ROOT/workflows/badgerdoc_ocr_${OCR_TAG}/main.py" \
  | grep -o '"[^"]*"' | head -1 | tr -d '"')
grep -q "\"temporal_queue\": \"$QUEUE\"" \
  "$REPO_ROOT/web/badgerdoc/fixtures/workflowregistry.json" \
  && echo "QUEUE MATCH OK ($QUEUE)" || echo "QUEUE MISMATCH: $QUEUE not found in fixture"

# 3. Env vars documented
OCR_TAG_UPPER=$(echo "$OCR_TAG" | tr '[:lower:]' '[:upper:]')
grep -q "OCR_\|${OCR_TAG_UPPER}" "$REPO_ROOT/.env_example" \
  && echo "ENV VARS OK" || echo "ENV VARS MISSING: nothing matching ${OCR_TAG_UPPER} in .env_example"

# 4. docker-compose service exists
grep -q "badgerdoc_ocr_${OCR_TAG}" "$REPO_ROOT/docker-compose.yml" \
  && echo "COMPOSE OK" || echo "COMPOSE MISSING: no service for badgerdoc_ocr_${OCR_TAG}"

# 5. Tag fixture entry exists (useTags() caches with staleTime: Infinity; fixture ensures fresh setups see the tag)
TAG_SLUG=$(echo "$OCR_TAG" | tr '_' '-')
grep -q "\"tag\": \"$TAG_SLUG\"" \
  "$REPO_ROOT/web/badgerdoc/fixtures/tags.json" \
  && echo "TAG FIXTURE OK ($TAG_SLUG)" || echo "TAG FIXTURE MISSING: $TAG_SLUG not in tags.json"

# 6 + 7. README.md exists, then package dependencies resolve
# (uv sync will fail if readme= is declared in pyproject.toml but the file is absent)
if test -f "$REPO_ROOT/workflows/badgerdoc_ocr_${OCR_TAG}/README.md"; then
  echo "README OK"
  (cd "$REPO_ROOT/workflows/badgerdoc_ocr_${OCR_TAG}" && uv sync) \
    && echo "UV SYNC OK" || echo "UV SYNC FAILED: fix pyproject.toml or add missing deps"
else
  echo "README MISSING: create workflows/badgerdoc_ocr_${OCR_TAG}/README.md"
  echo "UV SYNC SKIPPED: README.md must exist first (pyproject.toml readme= field)"
fi
```
