ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as build

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /opt/assets

COPY .env alembic.ini pyproject.toml poetry.lock version.txt ./
COPY alembic alembic
COPY assets assets

RUN : \
    && python3 -m pip install --upgrade pip \
    && pip install poetry>=1.1.13 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && :

RUN : \
    && apt-get update \
    && apt-get install -y poppler-utils \
    && apt-get install libmagic1 -y \
    && :

# CMD alembic upgrade afa33cc83d57 && alembic upgrade fe5926249504 && alembic upgrade 0f6c859c1d1c && alembic upgrade head
CMD uvicorn assets.main:app --host 0.0.0.0 --port 8080
EXPOSE 8080

FROM build AS development

COPY setup.cfg ./
COPY tests tests
RUN poetry install --no-root

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY --from=test /opt/assets/tests /opt/assets/tests
COPY --from=test /opt/assets/assets /opt/assets/assets
COPY --from=test /opt/assets/coverage.xml /opt/assets/coverage.xml
COPY sonar-project.properties /opt/assets/sonar-project.properties

RUN : \
    && ls -la /opt/assets/tests \
    && ls -la /opt/assets/assets \
    && cat /opt/assets/coverage.xml \
    && cat /opt/assets/sonar-project.properties \
    && :

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_ASSETS \
  -Dproject.settings=/opt/assets/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_ASSETS
