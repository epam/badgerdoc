ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base_3.12:0.2.0
FROM ${base_image} as build

ENV PYTHONUNBUFFERED 1

WORKDIR /opt/ml_server

COPY main.py pyproject.toml version.txt poetry.lock ./
RUN python3 -m pip install --upgrade pip \
    && pip install 'poetry>=2.0' -U \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && :

CMD uvicorn main:app --port 8080 --host 0.0.0.0

EXPOSE 8080

FROM build as development

RUN poetry install --no-root
