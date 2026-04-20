FROM badgerdoc-workflows-base

RUN mkdir -p /app/badgerdoc_ocr_dotsocr

WORKDIR /app/badgerdoc_ocr_dotsocr

COPY pyproject.toml uv.lock README.md ./

RUN mkdir -p badgerdoc_ocr_dotsocr badgerdoc_ocr_dotsocr/activities && \
    touch badgerdoc_ocr_dotsocr/__init__.py badgerdoc_ocr_dotsocr/activities/__init__.py

RUN uv sync --frozen

COPY . .

RUN ls -la

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]
