ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.8
FROM ${base_image} as build

WORKDIR /opt/convert

COPY poetry.lock pyproject.toml ./
COPY convert convert

RUN : \
   && apt-get update \
   && apt-get install --yes software-properties-common libmagickwand-dev \
   && add-apt-repository https://archive.ubuntu.com/ \
   && apt-get install -y ghostscript \
   && rm -rf /var/lib/apt/lists/* \
   && :

COPY policy.xml  /etc/ImageMagick-6/policy.xml

RUN : \
    && python3 -m pip install --upgrade pip \
    && pip install poetry>=1.1.13 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && :

CMD uvicorn convert.main:app --host 0.0.0.0 --port 8080
EXPOSE 8080

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY tests /working/tests
COPY convert /working/convert
COPY sonar-project.properties /working/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_MODELS \
  -Dproject.settings=/working/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_MODELS
