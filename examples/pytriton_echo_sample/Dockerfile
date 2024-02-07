FROM python:3.10.13-bookworm

WORKDIR /app

# install requirements file
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py /app/server.py

CMD python3 /app/server.py
