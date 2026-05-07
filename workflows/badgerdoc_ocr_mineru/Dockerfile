FROM badgerdoc-workflows-base

RUN mkdir -p /app/badgerdoc_ocr_mineru

WORKDIR /app/badgerdoc_ocr_mineru

COPY pyproject.toml uv.lock README.md ./
# improve re-build performance
RUN mkdir -p badgerdoc_ocr_mineru badgerdoc_ocr_mineru/activities && \
    touch badgerdoc_ocr_mineru/__init__.py badgerdoc_ocr_mineru/activities/__init__.py

RUN uv sync --frozen

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]
