FROM python:3.8.10-slim-buster AS base

COPY lib/filter_lib/ /opt/filter_lib/
COPY lib/tenants/ /opt/tenants/
RUN python3 -m pip install --upgrade pip && \
    apt update && \
    apt install gcc -y && \
    pip3 install poetry==1.4.0  && \
    cd /opt/filter_lib && pip3 install . && \
    cd /opt/tenants && pip3 install . && \
    cd ../ && rm -rf filter_lib && rm -rf tenants

ENV PYTHONPATH /opt

FROM base AS test

RUN pip install virtualenv

WORKDIR /opt/filter_lib
RUN python3 -m venv env
RUN . env/bin/activate && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt && isort src --check \
    && black src --check && mypy src && pylint src \
    && pytest -vv --cov --cov-report=xml && deactivate

WORKDIR /opt/tenant_dependency
RUN python3 -m venv env
RUN . env/bin/activate && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt && isort src --check \
    && black src --check && mypy src && pylint src \
    && pytest -vv --cov --cov-report=xml && deactivate 
