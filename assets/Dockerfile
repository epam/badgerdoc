ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as build

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /opt/dataset_manager

COPY .env alembic.ini Pipfile Pipfile.lock version.txt ./

RUN apt-get update -y && apt-get install -y poppler-utils \
    && apt-get install libmagic1 -y \
    && python3 -m pip install --upgrade pip && pip install pipenv \
    && pipenv install --system --deploy

COPY alembic alembic
COPY src src


CMD alembic upgrade afa33cc83d57 && alembic upgrade fe5926249504 && alembic upgrade 0f6c859c1d1c && alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8080

FROM build AS test

RUN pipenv install --system --deploy --dev

COPY setup.cfg ./
COPY tests tests
COPY src src


RUN isort src --check && black src -l 79 --check && mypy src && pylint --rcfile=setup.cfg src && pytest -vv --cov --cov-report=xml

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY --from=test /opt/dataset_manager/tests /opt/dataset_manager/tests
COPY --from=test /opt/dataset_manager/src /opt/dataset_manager/src
COPY --from=test /opt/dataset_manager/coverage.xml /opt/dataset_manager/coverage.xml
COPY sonar-project.properties /opt/dataset_manager/sonar-project.properties

RUN ls -la /opt/dataset_manager/tests && ls -la /opt/dataset_manager/src && cat /opt/dataset_manager/coverage.xml && cat /opt/dataset_manager/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_ASSETS \
  -Dproject.settings=/opt/dataset_manager/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_ASSETS
