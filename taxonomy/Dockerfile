ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as build

WORKDIR /opt/taxonomy

ENV PYTHONPATH /opt/taxonomy
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY pyproject.toml poetry.lock .env alembic.ini version.txt ./
COPY alembic alembic
COPY taxonomy taxonomy

RUN : \
    && python3 -m pip install --upgrade pip \
    && pip install poetry>=1.1.13 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && :

CMD alembic upgrade head && uvicorn taxonomy.main:app --host 0.0.0.0 --port 8080

FROM build as development

COPY Makefile pytest.ini setup.cfg ./
COPY tests tests
COPY documentation documentation
RUN poetry install --no-root
