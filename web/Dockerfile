ARG NODE_IMAGE=node:24.13-bookworm-slim
ARG BASE_IMAGE=python:3.12-slim

# Docs build
FROM ${BASE_IMAGE} AS docs-builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY web/pyproject.toml ./pyproject.toml
COPY web/uv.lock ./uv.lock
COPY web/README.md ./README.md
RUN uv sync --extra docs

COPY web/docs ./docs

RUN uv run mkdocs build -f /app/docs/mkdocs.yml

# Frontend build
FROM ${NODE_IMAGE} AS frontend-builder

WORKDIR /build
COPY web/frontend/ /build

RUN npm install && npm run build


# Web image
FROM ${BASE_IMAGE}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    DJANGO_SETTINGS_MODULE=badgerdoc.settings \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

RUN useradd --create-home --shell /bin/bash django
WORKDIR /app

COPY workflows/badgerdoc_common ./badgerdoc_common

COPY web/pyproject.toml ./pyproject.toml
COPY web/uv.lock ./uv.lock
COPY web/README.md ./README.md

RUN uv sync --frozen --no-dev && \
    rm -rf $UV_CACHE_DIR

COPY web/ .
COPY --from=frontend-builder /build/dist /app/staticfiles/badgerdoc-frontend
COPY --from=docs-builder /app/docs/site /app/docs/site
RUN mkdir -p /app/staticfiles && chown -R django:django /app



EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/admin/ || exit 1

# Create entrypoint script
COPY web/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
