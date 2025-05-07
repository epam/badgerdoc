ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base_3.12:0.2.0
FROM ${base_image} as build

WORKDIR /opt/jobs

COPY pyproject.toml poetry.lock .env alembic.ini version.txt ./
RUN : \
    && python3 -m pip install --upgrade pip \
    && pip install poetry>=1.1.13 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && :

COPY alembic alembic
COPY jobs jobs

CMD alembic upgrade head && uvicorn jobs.main:app --host 0.0.0.0 --port 8080
EXPOSE 8080

FROM build as development

RUN poetry install --no-root
COPY setup.cfg pytest.ini ./
COPY tests tests
