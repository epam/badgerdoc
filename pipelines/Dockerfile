ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.5
FROM ${base_image} as build

WORKDIR /opt/pipeline_executor

COPY src src
COPY alembic alembic
COPY alembic.ini wait-for-it.sh .env requirements.txt version.txt setup.py ./

RUN python3 -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt && pip install .

ENV PYTHONPATH /opt/pipeline_executor
CMD alembic upgrade head && uvicorn src.app:app --host 0.0.0.0 --port 8080

FROM build AS test

COPY setup.cfg requirements_dev.txt ./
COPY tests tests

RUN pip install --no-cache-dir -r requirements_dev.txt && python3 -m pip install types-requests

CMD isort src --check && black src -l 79 --check && mypy src && pylint --rcfile=setup.cfg src && pytest --cov

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY src /sonar/src
COPY alembic /sonar/alembic
COPY tests /sonar/tests
COPY sonar-project.properties /sonar/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_PIPELINES \
  -Dproject.settings=/sonar/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_PIPELINES
