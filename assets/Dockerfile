ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as build

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /opt/assets

COPY .env alembic.ini pyproject.toml poetry.lock version.txt ./
COPY alembic alembic
COPY assets assets


RUN : \
    && apt-get update \
    && apt install -y git gcc build-essential \
    && apt-get install -y poppler-utils \
    && apt-get install libmagic1 -y \
    && :

RUN : \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && :

CMD alembic upgrade afa33cc83d57 \
    && alembic upgrade fe5926249504 \
    && alembic upgrade 0f6c859c1d1c \
    && alembic upgrade head \
    && uvicorn assets.main:app --host 0.0.0.0 --port 8080

EXPOSE 8080

FROM build AS development

COPY setup.cfg ./
COPY tests tests
RUN poetry install --no-root
