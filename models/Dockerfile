ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install poetry

COPY pyproject.toml /

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-dev\
    && rm -rf pyproject.toml poetry.lock

RUN apt-get update && apt-get -y install curl unzip sshfs
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip  && rm awscliv2.zip && ./aws/install

FROM base AS build

WORKDIR /working

COPY src /working/src
COPY src /working/src
COPY alembic /working/alembic
COPY alembic.ini /working

ENV PYTHONPATH "$PYTHONPATH: src"

EXPOSE 8000

CMD alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8080


FROM build AS test

RUN pip install poetry

COPY pyproject.toml /

RUN poetry install

WORKDIR /working

COPY tests /working/tests

RUN isort --profile=black --line-length=79 .

RUN black --line-length=79 .

RUN mypy --ignore-missing-imports --scripts-are-modules --allow-untyped-decorators --strict  --no-strict-optional src/

RUN pylint --max-line-length=79 --errors-only --disable=E0401,E0611 src/

RUN python3 -m pytest --cov=src tests/ -m "not integration"

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY tests /working/tests
COPY src /working/src
COPY sonar-project.properties /working/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_MODELS \
  -Dproject.settings=/working/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_MODELS

FROM base as build-dev

RUN poetry install --no-root
CMD alembic upgrade head && uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
