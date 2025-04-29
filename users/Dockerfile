ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base_3.12:0.2.0
FROM ${base_image} as build

WORKDIR /opt/users

COPY users ./users
COPY pyproject.toml poetry.lock .env version.txt ./

RUN : \
    && apt-get update \
    && apt-get install -y build-essential \
    && :

RUN : \
    && python3 -m pip install --upgrade pip \
    && pip install poetry>=1.7.1 \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && :

CMD ["uvicorn", "users.main:app", "--host", "0.0.0.0", "--port", "8080"]
EXPOSE 8080
