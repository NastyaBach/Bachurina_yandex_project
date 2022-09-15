FROM python:3.9.0

ARG WORKDIR=/app

COPY requirements.txt .
RUN pip install -r requirements.txt
