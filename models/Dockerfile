ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as build

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /opt/models

COPY pyproject.toml poetry.lock alembic.ini ./
COPY models models
COPY alembic alembic

RUN : \
    && python3 -m pip install --upgrade pip \
    && pip install poetry~=1.4.0 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && :

CMD alembic upgrade head && uvicorn models.main:app --host 0.0.0.0 --port 8080
EXPOSE 8080

FROM build AS build-dev

COPY pytest.ini ./
COPY tests tests
RUN poetry install --no-root

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

WORKDIR /opt/models

COPY tests tests
COPY models models
COPY sonar-project.properties sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_MODELS \
  -Dproject.settings=/opt/models/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_MODELS

FROM build-dev as test

RUN poetry run isort --profile=black --line-length=79 .
RUN poetry run black --line-length=79 .
RUN poetry run mypy --ignore-missing-imports --scripts-are-modules --allow-untyped-decorators --strict  --no-strict-optional models/
RUN poetry run pylint --max-line-length=79 --errors-only --disable=E0401,E0611 models/
RUN poetry run python3 -m pytest --cov=models tests/ -m "not integration"
