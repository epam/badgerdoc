FROM python:3.8.10-slim-buster AS base

RUN mkdir /opt/filter_lib && mkdir /opt/tenant_dependency
COPY filter_lib/ /opt/filter_lib
COPY tenant_dependency/ /opt/tenant_dependency
RUN python3 -m pip install --upgrade pip

FROM base AS test

RUN pip install virtualenv

WORKDIR /opt/filter_lib
RUN python3 -m venv env
RUN . env/bin/activate && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt \  
    # && isort src --check \
    # && black src --check && mypy src && pylint src \
    && pytest -vv --cov --cov-report=xml && deactivate

WORKDIR /opt/tenant_dependency
RUN python3 -m venv env
RUN . env/bin/activate && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt \ 
# && isort src --check \
    # && black src --check && mypy src && pylint src \
    && pytest -vv --cov --cov-report=xml && deactivate

FROM base AS build

WORKDIR /opt/filter_lib
RUN python3 setup.py install

WORKDIR /opt/tenant_dependency
RUN python3 setup.py install

WORKDIR /opt
ENV PYTHONPATH /opt
RUN rm -rf filter_lib && rm -rf tenant_dependency
RUN pip uninstall certifi -y
