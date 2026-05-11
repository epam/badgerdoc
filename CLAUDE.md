# CLAUDE.md

This file provides guidance to AI agents when working with code in this repository.

## Project Overview

Badgerdoc is a document pipeline — upload PDFs/images, get structured extraction results via multiple OCR engines, review and annotate results in a web UI. It is a Django + React monolith backed by Temporal workflows for async OCR processing.

## Commands

### Full Stack

```bash
# First-time setup
cp .env_example .env
make build_all                    # builds frontend + workflow base Docker image

# Start all services
docker compose up --build

# Post-setup (first run only)
docker compose exec web uv run python manage.py createsuperuser
docker compose exec web uv run python manage.py drf_create_token admin
# Add BADGERDOC_TOKEN=<token> to .env
# Create bucket 'badgerdoc' in MinIO at http://localhost:9001 (minioadmin/minioadmin)
```

### Tests

```bash
# Django tests (requires running stack)
make test
make test_specific TEST=badgerdoc.tests.test_document

# Frontend (from web/frontend/)
npm test              # vitest watch
npm run test:run      # single run
npm run test:coverage

# Per-workflow package
cd workflows/badgerdoc_convert && uv run pytest
```

### Code Quality

```bash
make quality_gate     # black + isort + mypy + pylint + bandit
make black            # format
make isort
make mypy             # type-checks web/ and workflows/
make pylint
```

### Frontend Dev

```bash
cd web/frontend
npm run dev           # Vite dev server
npm run build         # production build → Django staticfiles
npm run lint
npm run types:check
```

### MLX VLM Servers (macOS Apple Silicon only)

```bash
uv sync --group mlx
make start_mlx        # starts 3 VLM inference servers on ports 11434–11436
# Add to /etc/hosts: 127.0.0.1 minio
```

## Architecture

### Services

| Service | Tech | Role |
|---|---|---|
| `badgerdoc` (nginx) | Nginx | Entry point on :80; proxies to `web:8000` and WebSocket `/ws/` |
| `web` | Django 5.2 + Gunicorn | REST API + React SPA; API docs at `/swagger/` and `/redoc/` |
| `db` | PostgreSQL 15 | Primary database (SQLite supported via `BADGERDOC_DB_ENGINE=sqlite`) |
| `minio` | MinIO | S3-compatible object storage on :9001 |
| `temporal` | Temporal 1.29.3 | Workflow engine on :7233; UI on :8080 |
| `badgerdoc_lifecycle` | Python worker | Orchestration hub — dispatches child workflows |
| `badgerdoc_convert` | Python worker (5 replicas) | PDF→PNG and PNG→DZI conversion |
| `badgerdoc_ocr_*` | Python workers | OCR engines: PaddleOCR-VL, MinerU, DeepSeek-OCR-2, DotsOCR |
| `badgerdoc_ocr_arbitrator` | Python worker | AI judge that selects best OCR result across engines |

### Request / Event Flow

1. User uploads a document via the React SPA → Django API saves it, stores file in S3/MinIO.
2. Django `post_save` signals trigger `BadgerdocLifecycleWorkflow` on entity events (Document/Task/Extraction create/update).
3. `BadgerdocLifecycleWorkflow` queries the `WorkflowRegistry` model, finds matching workflows by `document_types`, `entity_tags`, `trigger` (auto/manual), and `extraction_scope`, then fan-outs to child workflows concurrently.
4. Each OCR worker: fetches source file from S3 → runs OCR → calls back to the Django API (`TEMPORAL_BADGERDOC_ADDRESS` + `BADGERDOC_TOKEN`) → stores results as hOCR in `ExtractionPage` records.
5. The arbitrator compares hOCR outputs from multiple engines and selects the best one.
6. Frontend polls for results via TanStack Query; document viewer uses OpenSeadragon with DZI tiles.

### Key Design Decisions

- **`WorkflowRegistry`** is the configuration hub: Django admin entries determine which Temporal workflows fire automatically for which document types and entity events. Adding a new OCR engine means adding a worker and a `WorkflowRegistry` entry.
- **`task_queue` name = package name** (e.g. `badgerdoc_convert`). Every worker registers on this queue name.
- **S3 path convention**: `tmp/workflows/<pkg>/<workflow_type>/<workflow_id>/` (temp) and `data/workflows/<pkg>/<workflow_type>/<workflow_id>/` (permanent).
- **Sub-workflows are called by string name** (`WorkflowType`) never by class reference.
- **All workflow logic lives in Temporal activities** — nothing substantive in `workflow.run()` methods.
- **Workers call back to the Django API** using the `badgerdoc_common` HTTP client with bearer token auth. They never write directly to the database.

### Code Layout

```text
web/badgerdoc/          # Django models, views, serializers, signals, settings
web/frontend/src/       # React SPA: routes/, components/, hooks/, api/, stores/
workflows/badgerdoc_common/         # Shared: HTTP client, S3 helpers, Temporal base classes, hOCR types
workflows/badgerdoc_lifecycle/      # Orchestration worker
workflows/badgerdoc_convert/        # Image conversion worker
workflows/badgerdoc_ocr_*/          # OCR engine workers
```

## Tech Stack

- **Python**: 3.12, managed with `uv`, built with `hatchling`
- **Django**: 5.2, Django REST Framework 3.15, drf-yasg for API docs
- **Frontend**: React 19, Vite 7, TanStack Router + Query, Radix UI, Tailwind CSS 4, Tiptap 3 (rich text), OpenSeadragon 4 (DZI viewer), Zustand 5
- **Frontend tests**: Vitest 4 + Testing Library + MSW (mock service worker) + happy-dom
- **Temporal SDK**: `>=1.18.2` (Python async SDK)
- **OCR output format**: hOCR (HTML-based, via `hocr-spec`)
- **Async in workers**: `aiohttp` (HTTP), `aioboto3` (S3)

## Coding Conventions

- Line length: **79 characters** (black + pylint configured)
- Use **async packages everywhere except Django** (synchronous Django for web, async for Temporal workers)
- Classes get their own modules; **prefer functions** over methods where possible
- No bash scripts in application code; Python only
- Docstrings are intentionally minimal
- Follow 12-factor app principles for configuration (all env-based)
- Google Python Style Guide + PEP8
