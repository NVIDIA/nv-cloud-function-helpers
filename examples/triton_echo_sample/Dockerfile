FROM nvcr.io/nvidia/tritonserver:24.01-py3

# install requirements file
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 安装 OpenTelemetry Collector
RUN apt-get update && apt-get install -y wget && \
    wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.91.0/otelcol-contrib_0.91.0_linux_amd64.tar.gz && \
    tar -xzf otelcol-contrib_0.91.0_linux_amd64.tar.gz -C /usr/local/bin && \
    rm otelcol-contrib_0.91.0_linux_amd64.tar.gz && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY model_repository /model_repository
COPY agent-collector-config.yaml /etc/otel/agent-collector-config.yaml
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV CUDA_MODULE_LOADING LAZY
ENV LOG_VERBOSE 0

CMD ["/start.sh"]
