ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base:0.1.5
FROM ${base_image} as build

WORKDIR /usr/src

RUN pip install -U pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scheduler scheduler
COPY .env .

COPY alembic alembic
COPY alembic.ini .

ENV PYTHONPATH /usr/src

CMD alembic upgrade head && uvicorn scheduler.app:app --host 0.0.0.0 --port 8002
