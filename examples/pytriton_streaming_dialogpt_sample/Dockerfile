FROM nvcr.io/nvidia/pytorch:23.10-py3

WORKDIR /app

# install requirements file
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py /app/server.py

ENV CUDA_MODULE_LOADING LAZY
ENV LOG_VERBOSE 0

CMD python /app/server.py --model-name microsoft/DialoGPT-small
