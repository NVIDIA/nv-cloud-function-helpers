FROM python:3.10

WORKDIR /app

COPY client/requirements.txt ./

RUN python -m pip install --no-cache-dir -U pip && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY echo.proto /app/
RUN python -m grpc_tools.protoc -I /app/  --python_out=. --pyi_out=. --grpc_python_out=. /app/echo.proto

COPY client/client.py /app/

CMD python3 /app/client.py
