ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base_3.12:0.2.0
FROM ${base_image} as build

ENV PYTHONPATH /opt/annotation
WORKDIR /opt/annotation

COPY pyproject.toml poetry.lock .env alembic.ini version.txt ./
COPY alembic alembic
COPY annotation annotation
COPY documentation documentation

RUN : \
    && python3 -m pip install --upgrade pip \
    && pip install poetry==1.7.1 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main


CMD alembic upgrade head && uvicorn annotation.main:app --root-path $ROOT_PATH --reload --host 0.0.0.0 --port 8080
EXPOSE 8080

FROM base as test

COPY Makefile pytest.ini setup.cfg ./
COPY tests tests
COPY annotation annotation
COPY alembic alembic

RUN apt-get install -y make
RUN poetry install --no-root
RUN make test_checks

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar-annotation

COPY --from=test /opt/annotation/tests /opt/annotation/tests
COPY --from=test /opt/annotation/annotation /opt/annotation/annotation
COPY --from=test /opt/annotation/alembic /opt/annotation/alembic
COPY sonar-project.properties /opt/annotation/sonar-project.properties

RUN ls -la /opt/annotation/tests && ls -la /opt/annotation/annotation && cat /opt/annotation/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_ANNOTATION \
  -Dproject.settings=/opt/annotation/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_ANNOTATION

FROM base as build-dev

RUN poetry install --no-root
CMD alembic upgrade head && uvicorn annotation.main:app --root-path $ROOT_PATH --reload --host 0.0.0.0 --port 8080
