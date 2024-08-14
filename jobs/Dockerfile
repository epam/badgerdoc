ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.8
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

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY --from=test /opt/jobs/tests /opt/jobs/tests
COPY --from=test /opt/jobs/jobs /opt/jobs/jobs
COPY sonar-project.properties /opt/sonar/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_JOBS \
  -Dproject.settings=/opt/sonar/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_JOBS
