ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.6
FROM ${base_image} as base

ENV PYTHONPATH /opt
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Poetry
RUN apt-get update && apt-get -qq -y install curl
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | \
    POETRY_HOME=/opt/taxonomy/poetry python && cd /usr/local/bin && \
    ln -s /opt/taxonomy/poetry/bin/poetry && poetry config virtualenvs.create false

# Copy using poetry.lock in case it doesn't exist yet
COPY pyproject.toml poetry.lock .env alembic.ini version.txt ./
COPY ./alembic ./alembic
COPY ./app ./app

FROM base as build

RUN poetry install --no-root --no-dev
COPY ./documentation ./documentation
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8080

FROM base as test

RUN apt-get install -y make
RUN poetry install --no-root
COPY Makefile pytest.ini setup.cfg ./
COPY ./tests ./tests
COPY app app
COPY alembic alembic
RUN make test_checks

FROM base as build-dev

RUN poetry install --no-root
CMD alembic upgrade head && uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
