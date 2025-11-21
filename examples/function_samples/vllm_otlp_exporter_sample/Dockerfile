FROM vllm/vllm-openai:v0.11.2

WORKDIR /app

# install the OpenTelemtry Collector
ENV OTEL_VERSION=0.140.0
RUN apt-get update
RUN apt-get -y install wget systemctl git python3 python3-pip
RUN apt-get -y install jq
RUN wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v${OTEL_VERSION}/otelcol-contrib_${OTEL_VERSION}_linux_amd64.deb
RUN dpkg -i otelcol-contrib_${OTEL_VERSION}_linux_amd64.deb

# configure vllm logging
COPY vllm_logging_config.json /app/vllm_logging_config.json
ENV VLLM_LOGGING_CONFIG_PATH=/app/vllm_logging_config.json

# add configuration for the otel collector
ENV OTEL_SERVICE_NAME="vllm"
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
COPY otel-collector-config.yaml /etc/otel-collector-config.yaml
RUN otelcol-contrib validate --config=/etc/otel-collector-config.yaml

# copy the entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]