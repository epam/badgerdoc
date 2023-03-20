ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as build

ENV PYTHONPATH /usr/scheduler
WORKDIR /usr/scheduler

COPY alembic alembic
COPY scheduler scheduler
COPY poetry.lock pyproject.toml .env alembic.ini version.txt ./

RUN : \
    && python3 -m pip install --upgrade pip \
    && pip install poetry>=1.1.13 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --only main \
    && :


CMD alembic upgrade head && uvicorn scheduler.app:app --host 0.0.0.0 --port 8002

FROM build as tests

COPY tests tests
RUN poetry install --no-root
