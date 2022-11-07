ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as base

ENV PYTHONPATH /opt
WORKDIR /opt/search

RUN apt-get update && apt-get -y install curl
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | \
    POETRY_HOME=/opt/search/poetry python && cd /usr/local/bin && \
    ln -s /opt/search/poetry/bin/poetry && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock .env version.txt ./
COPY search search

FROM base as build

RUN poetry install --no-root --no-dev
COPY documentation documentation
CMD ["uvicorn", "search.main:app", "--host", "0.0.0.0", "--port", "8080"]

FROM base as test

RUN apt-get install -y make
RUN poetry install --no-root
COPY Makefile pytest.ini setup.cfg ./
COPY tests tests
RUN make test_checks

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY search /sonar/search
COPY tests /sonar/tests
COPY sonar-project.properties /sonar/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_SEARCH \
  -Dproject.settings=/sonar/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_SEARCH

FROM base as build-dev

RUN poetry install --no-root --no-dev
COPY documentation documentation
CMD ["uvicorn", "search.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
