ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.7
FROM ${base_image} as build

WORKDIR /opt/users_filter

COPY src /opt/users_filter/src
COPY requirements.txt /opt/users_filter
COPY .env /opt/users_filter

RUN python3 -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM build AS test

COPY requirements_dev.txt ./
COPY tests tests
RUN pip install --no-cache-dir -r requirements_dev.txt

CMD pytest -vvv

FROM sonarsource/sonar-scanner-cli:4.6 AS sonar

COPY src /sonar/src
COPY tests /sonar/tests
COPY sonar-project.properties /sonar/sonar-project.properties

CMD sonar-scanner \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY_USERS \
  -Dproject.settings=/sonar/sonar-project.properties \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN_USERS
