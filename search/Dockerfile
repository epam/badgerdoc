ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as build

#RUN python3 -m pip install --upgrade pip && \
#    apt update && \
#    apt install gcc -y && \
#    pip3 install poetry==1.4.0

ENV PYTHONPATH /opt/search
WORKDIR /opt/search

COPY pyproject.toml poetry.lock .env version.txt ./
COPY search search

RUN : \
    && python3 -m pip install --upgrade pip \
    && pip install poetry>=1.1.13 \
    && poetry config virtualenvs.create false \
    && :

COPY documentation documentation
RUN poetry install --no-root --only main
CMD ["uvicorn", "search.main:app", "--host", "0.0.0.0", "--port", "8080"]

FROM base as test

COPY Makefile pytest.ini setup.cfg ./
COPY tests tests
RUN apt-get install -y make
RUN poetry install --no-root
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

RUN poetry install --no-root
COPY documentation documentation
CMD ["uvicorn", "search.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
