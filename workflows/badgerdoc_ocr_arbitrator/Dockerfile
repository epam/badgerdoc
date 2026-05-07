FROM badgerdoc-workflows-base

RUN mkdir -p /app/badgerdoc_ocr_arbitrator

WORKDIR /app/badgerdoc_ocr_arbitrator

COPY pyproject.toml ./
COPY . .

RUN ls -la

RUN uv sync --frozen

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]