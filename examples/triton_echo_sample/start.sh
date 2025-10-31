#!/bin/bash
set -e

# 启动 OpenTelemetry Collector 在后台
echo "Starting OpenTelemetry Collector..."
/usr/local/bin/otelcol-contrib --config=/etc/otel/agent-collector-config.yaml &

# 等待 Collector 启动
sleep 2

# 启动 Triton Server
echo "Starting Triton Server..."
tritonserver --log-verbose ${LOG_VERBOSE} --http-header-forward-pattern nvcf-.* \
    --model-repository /model_repository/ --model-control-mode=none --strict-readiness 1 \
    --allow-metrics 1 --allow-gpu-metrics 1 --allow-cpu-metrics 1 --metrics-interval-ms 500

