FROM python:3.12-alpine3.20

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dsx_connect/ dsx_connect/

ENV PYTHONPATH=/app

# Command is set in docker-compose.yaml