ARG base_image=818863528939.dkr.ecr.eu-central-1.amazonaws.com/badgerdoc/python_base_3.12:0.2.0
FROM ${base_image}

WORKDIR /opt/ml_server

COPY main.py requirements.txt ./

RUN pip3 install -r requirements.txt

CMD uvicorn main:app --port 8080 --host 0.0.0.0

EXPOSE 8080
