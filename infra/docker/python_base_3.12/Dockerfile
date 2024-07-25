FROM python:3.12.1-bookworm AS base

COPY lib/filter_lib/ /opt/filter_lib/
COPY lib/tenants/ /opt/tenants/
COPY lib/badgerdoc_storage /opt/badgerdoc_storage/

RUN python3 -m pip install --upgrade pip && \
    apt update && \
    apt install gcc -y && \
    pip3 install poetry==1.7.1  && \
    cd /opt/filter_lib && pip3 install . && \
    cd /opt/tenants && pip3 install . && \
    cd ../ && rm -rf filter_lib && rm -rf tenants && rm -rf badgerdoc_storage

ENV PYTHONPATH /opt
