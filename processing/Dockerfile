ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as base

ENV PYTHONUNBUFFERED 1
WORKDIR /processing

COPY poetry.lock pyproject.toml .env alembic.ini version.txt ./

RUN : \
    && python3 -m pip install --upgrade pip \
    && pip install poetry~=1.4.0 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && :

FROM base as build

COPY alembic alembic
COPY processing processing
CMD alembic upgrade head && uvicorn processing.main:app --host 0.0.0.0 --port 8080
EXPOSE 8080

FROM build as development

COPY tests/ tests/
RUN poetry install --no-root

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY package/processing /sonar/processing
COPY package/tests /sonar/tests
COPY sonar-project.properties /sonar/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_PROCESSING \
  -Dproject.settings=/sonar/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_PROCESSING
