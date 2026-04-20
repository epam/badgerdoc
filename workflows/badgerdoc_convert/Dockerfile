FROM badgerdoc-workflows-base

RUN mkdir -p /app/badgerdoc_convert

WORKDIR /app/badgerdoc_convert

COPY pyproject.toml ./
COPY . .

RUN ls -la

RUN uv sync --frozen

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]
