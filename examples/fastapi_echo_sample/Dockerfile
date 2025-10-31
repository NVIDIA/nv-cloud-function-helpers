FROM python:3.13.7-bookworm

ENV WORKER_COUNT=10

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --no-cache-dir -U pip && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY http_echo_server.py /app/

CMD python /app/http_echo_server.py