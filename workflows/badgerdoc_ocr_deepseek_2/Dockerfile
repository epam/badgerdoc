FROM badgerdoc-workflows-base

RUN mkdir -p /app/badgerdoc_ocr_deepseek_2

WORKDIR /app/badgerdoc_ocr_deepseek_2

COPY pyproject.toml ./
COPY . .

RUN ls -la

RUN uv sync --frozen

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]
