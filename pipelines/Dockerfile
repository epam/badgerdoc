ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as build

ENV PYTHONPATH /opt/pipelines
WORKDIR /opt/pipelines

COPY pipelines pipelines
COPY alembic alembic
COPY alembic.ini wait-for-it.sh .env pyproject.toml poetry.lock version.txt ./

RUN : \
    && python3 -m pip install --upgrade pip \
    && pip install poetry>=1.1.13 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && :

CMD alembic upgrade head && uvicorn pipelines.app:app --host 0.0.0.0 --port 8080

FROM build AS development

COPY setup.cfg ./
COPY tests tests
RUN poetry install --no-root

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY pipelines /sonar/pipelines
COPY alembic /sonar/alembic
COPY tests /sonar/tests
COPY sonar-project.properties /sonar/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_PIPELINES \
  -Dproject.settings=/sonar/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_PIPELINES
