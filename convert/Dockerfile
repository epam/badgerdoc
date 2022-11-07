ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.4
FROM ${base_image} as base

RUN apt-get update \
   && apt-get install --yes software-properties-common libmagickwand-dev \
   && add-apt-repository https://archive.ubuntu.com/ \
   && apt-get install -y ghostscript \
   && rm -rf /var/lib/apt/lists/*

COPY policy.xml  /etc/ImageMagick-6/policy.xml


RUN pip install poetry
COPY poetry.lock pyproject.toml /
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-dev\
    && rm -rf pyproject.toml poetry.lock


FROM base as build
#ENV ROOT_PATH="/api/v1/convert"
WORKDIR /convert
COPY src/ /convert/src
CMD uvicorn src.main:app --host 0.0.0.0 --port 8080


FROM base as test
CMD ["python", "-m", "pytest", "--cov=app"]


FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY tests /working/tests
COPY src /working/src
COPY sonar-project.properties /working/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_MODELS \
  -Dproject.settings=/working/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_MODELS
