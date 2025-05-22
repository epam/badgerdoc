ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base_3.12:0.2.0
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
    && pip install poetry>=1.7.1 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && :

CMD alembic upgrade head && uvicorn taxonomy.main:app --root-path $ROOT_PATH --host 0.0.0.0 --port 8080
EXPOSE 8080

FROM build as development

COPY Makefile pytest.ini setup.cfg ./
COPY tests tests
COPY documentation documentation
RUN poetry install --no-root
