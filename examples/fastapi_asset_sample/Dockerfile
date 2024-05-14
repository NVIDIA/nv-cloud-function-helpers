FROM python:3.10.13-bookworm

ENV WORKER_COUNT=10

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --no-cache-dir -U pip && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY http_server.py /app/

CMD uvicorn http_server:app --host=0.0.0.0 --workers=$WORKER_COUNT