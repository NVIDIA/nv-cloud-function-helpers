FROM python:3.10

WORKDIR /app

COPY client/requirements.txt ./

RUN python -m pip install --no-cache-dir -U pip && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY client/client.py /app/

CMD python3 /app/client.py
