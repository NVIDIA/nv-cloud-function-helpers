FROM nvcr.io/nvidia/cuda:12.3.1-devel-ubuntu22.04
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    python-is-python3 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace/
# install requirements file
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
ENV DEBIAN_FRONTEND=noninteractive
#copy source code
COPY main.py .
ENV CUDA_MODULE_LOADING LAZY
ENV LOG_VERBOSE 0
CMD python3 main.py
