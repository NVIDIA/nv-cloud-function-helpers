FROM nvcr.io/nvidia/tritonserver:24.01-py3

# install requirements file
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY model_repository /model_repository

ENV CUDA_MODULE_LOADING LAZY
ENV LOG_VERBOSE 0

CMD tritonserver --log-verbose ${LOG_VERBOSE} --http-header-forward-pattern (nvcf-.*|NVCF-.*) \
    --model-repository /model_repository/ --model-control-mode=none --strict-readiness 1 \
    --allow-metrics 1 --allow-gpu-metrics 1 --allow-cpu-metrics 1 --metrics-interval-ms 500 \
    --trace-config mode=opentelemetry --trace-config rate=1 --trace-config level=TIMESTAMPS \
    --trace-config opentelemetry,resource=url=${NVCF_TRACING_ENDPOINT_HTTP}
