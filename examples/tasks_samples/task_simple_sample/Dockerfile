FROM python:3.12-bullseye

COPY requirements.txt ./

RUN python -m pip install --no-cache-dir -U pip && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["python3", "main.py"]