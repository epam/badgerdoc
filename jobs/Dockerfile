ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as build

WORKDIR /opt/job_manager

COPY requirements.txt .env alembic.ini version.txt ./
RUN python3 -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY alembic alembic
COPY jobs jobs

CMD alembic upgrade head && uvicorn jobs.main:app --host 0.0.0.0 --port 8123

FROM build as test

COPY requirements-dev.txt setup.cfg pytest.ini ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY tests tests

CMD isort jobs --check && black jobs -l 79 --check && mypy jobs && pylint --rcfile=setup.cfg jobs && pytest -vv --cov --cov-report=xml

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY --from=test /opt/job_manager/tests /opt/job_manager/tests
COPY --from=test /opt/job_manager/jobs /opt/job_manager/jobs
COPY sonar-project.properties /opt/sonar/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_JOBS \
  -Dproject.settings=/opt/sonar/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_JOBS
