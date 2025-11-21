#!/bin/bash

set -e

# start the otel collector
otelcol-contrib --config /etc/otel-collector-config.yaml &

# start the vllm server
vllm serve