FROM badgerdoc-workflows-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libxcb1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/badgerdoc_ocr_mineru

WORKDIR /app/badgerdoc_ocr_mineru

COPY pyproject.toml uv.lock README.md ./
# improve re-build performance
RUN mkdir -p badgerdoc_ocr_mineru badgerdoc_ocr_mineru/activities && \
    touch badgerdoc_ocr_mineru/__init__.py badgerdoc_ocr_mineru/activities/__init__.py

RUN uv sync --frozen

COPY . .

RUN ls -la

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]
