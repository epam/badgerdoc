FROM apache/airflow:2.7.0

COPY requirements.txt ./

RUN pip3 install -r requirements.txt \
    && rm requirements.txt

RUN echo >> /home/airflow/.local/lib/python3.8/site-packages/airflow/cli/cli_config.py && \
    echo 'ARG_AUTOSCALE = Arg(("-a", "--autoscale"), help="Minimum and Maximum number of worker to autoscale")' >> /home/airflow/.local/lib/python3.8/site-packages/airflow/cli/cli_config.py