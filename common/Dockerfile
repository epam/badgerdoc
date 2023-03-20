#
FROM python:3.8.10-slim-buster as base

RUN apt-get update \
   && apt-get install --yes software-properties-common libmagickwand-dev \
   && add-apt-repository https://archive.ubuntu.com/ \
   && apt-get install -y ghostscript \
   && rm -rf /var/lib/apt/lists/*

COPY policy.xml  /etc/ImageMagick-6/policy.xml

WORKDIR /common/services
COPY services /common/services

WORKDIR /common/minio_service
COPY minio_service/ /common/minio_service

ARG ARTIFACTORY_USER
ARG ARTIFACTORY_PASS

RUN pip install poetry>=1.1.13

COPY minio_service/pyproject.toml /common/minio_service
COPY minio_service/poetry.lock /common/minio_service

RUN poetry config virtualenvs.create false \
   && poetry build\
   && tar xvzf dist/minio-service-0.1.0.tar.gz\
   && poetry install --no-interaction --only main\
   && poetry run add-logging\
   && rm -rf pyproject.toml poetry.lock

RUN python3 -m pip install --upgrade pip && python3 setup.py install

WORKDIR /common/page_rendering
COPY page_rendering /common/page_rendering

COPY page_rendering/pyproject.toml /common/page_rendering
COPY page_rendering/poetry.lock /common/page_rendering

RUN poetry config virtualenvs.create false \
   && poetry build\
   && tar xvzf dist/page_rendering-0.1.0.tar.gz\
   && poetry install --no-interaction --only main\
   && poetry run add-logging\
   && rm -rf pyproject.toml poetry.lock

RUN python3 setup.py install

COPY tests /common/tests
WORKDIR /common

RUN rm -rf minio_service && rm -rf page_rendering

#
FROM base AS build
CMD ["/bin/bash"]

# 'push' is addtitional layer for push code to artifactory pypi repo. Look at the Makefile.
# for troubleshooting find container id into the pipeline bild log and check containers log on the giltab-runner server
FROM build as push
WORKDIR /model_api
COPY model_api/ /model_api/
RUN poetry build
CMD poetry config repositories.epam_registry https://artifactory.epam.com/artifactory/api/pypi/EPM-UII-PyPI && \
    poetry publish -r epam_registry --username $ARTIFACTORY_USER --password $ARTIFACTORY_PASS

#
FROM base as test
RUN pip install pytest
WORKDIR /common/tests
CMD ["python3", "-m", "pytest", ""]
