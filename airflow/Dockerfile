FROM apache/airflow:2.8.0

COPY requirements.txt ./

RUN pip3 install -r requirements.txt \
    && rm requirements.txt
