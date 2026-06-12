# AGENTS.md

Cross-agent guidance for AI coding agents working in this repository.

This file is a lightweight bridge for agents that read `AGENTS.md`. It should
not duplicate the full project guide.

Before making changes, read `CLAUDE.md` for detailed project context, setup and
test commands, architecture, tech stack, code layout, state management,
frontend/backend conventions, and testing expectations.

If guidance conflicts, actual repository files are the source of truth:
`Makefile`, `package.json`, `pyproject.toml`, test config, Docker config,
generated-file headers, and nearby implementation. Prefer repository files
first, then `CLAUDE.md`, then this file. Mention any mismatch in the final
response.

## Agent Workflow

- Inspect existing implementation and nearby tests before editing.
- Prefer focused, minimal changes that match surrounding patterns.
- Reuse existing components, hooks, adapters, utilities, models, workflow base
  classes, and design-system patterns before adding new ones.
- Avoid unrelated refactors, formatting churn, dependency changes, and generated
  file edits.
- For UI/API changes, update connected layers consistently: adapter types,
  real adapter, mock adapter/MSW data, React Query hooks, feature UI, and tests.
- Do not invent backend endpoints, mock fields, frontend types, or new
  abstractions without checking existing contracts and patterns.
- Keep route files thin; put larger UI and business logic in feature modules.
- Workflow workers must call back through the Django API and must not write
  directly to the database.

## Validation

Prefer targeted validation first. Broaden only when the change crosses
frontend/backend/workflow boundaries, touches shared contracts, changes data
shape, or affects risky document-review behavior.

Use the commands documented in `CLAUDE.md` and the repository config. Do not
copy command lists into this file.

If validation cannot be run, explain what was skipped, why it was skipped, and
what risk remains.

## UI Product Principles

- Keep document review, workspace, viewer, and editor screens dense,
  functional, and task-focused.
- Avoid decorative or marketing-style UI, oversized hero sections, and
  unnecessary explanatory text for operational workflows.
- Preserve stable Tiptap/OpenSeadragon behavior and the boundary between editor
  state and viewer state.
- Be careful with dirty/unsaved state, text selection, highlights, tabs,
  popovers, zoom, viewport position, and current-page synchronization.

## Risky Areas

Be extra careful around:

- dirty/unsaved state and save prompts;
- extraction approve, reject, revert, and status transition flows;
- highlight synchronization between hOCR/editor content and viewer overlays;
- OpenSeadragon viewport, zoom, tile loading, selection, and current-page sync;
- route/search params, tab state, and persisted table/view preferences;
- consistency between adapter types, real API adapters, mock adapters, MSW data,
  and React Query hooks;
- workflow callback payloads, bearer-token auth, S3 paths, and
  `WorkflowRegistry` matching logic.

## Security

- Never commit `.env`, tokens, secrets, generated credentials, or local data.
- Do not log tokens, authorization headers, cookies, signed URLs, or sensitive
  document contents.
- Treat uploaded documents and extracted OCR text as sensitive user data.

## Generated Files

- Do not edit generated files manually, especially
  `web/frontend/src/routeTree.gen.ts`.
- If generated output must change, update the source or config that generates it
  and run the appropriate generator/build command from `CLAUDE.md` or repo
  config.

## Definition of Done

- The implementation matches existing patterns and keeps the change focused.
- Relevant tests were added or updated for behavior changes.
- Connected UI/API/mock layers were updated consistently.
- Generated files were not edited manually.
- Targeted validation was run first, or skipped with a clear reason.
- Final response lists changed files, validation commands, skipped checks,
  assumptions, risks, and follow-ups.
