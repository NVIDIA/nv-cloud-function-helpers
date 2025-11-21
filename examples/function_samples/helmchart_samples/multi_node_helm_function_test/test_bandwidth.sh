#!/usr/bin/env bash

set -e

# Load configuration from config.env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.env"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: config.env not found!"
    echo "Please create config.env from config.env.sample:"
    echo "  cp config.env.sample config.env"
    echo "Then edit config.env with your API key and function ID."
    exit 1
fi

source "$CONFIG_FILE"

# Validate required variables
if [ -z "$KEY" ] || [ "$KEY" = "your-api-key-here" ]; then
    echo "Error: KEY not set in config.env"
    exit 1
fi

if [ -z "$FUNCTION_ID" ] || [ "$FUNCTION_ID" = "your-multi-node-function-id" ] || [ "$FUNCTION_ID" = "your-single-node-function-id" ]; then
    echo "Error: FUNCTION_ID not set in config.env"
    exit 1
fi

# Test 1: Run all bandwidth tests with default settings
# echo "======================================================================================================"
# echo " Test 1: Running all bandwidth tests with default settings"
# echo "======================================================================================================"
# RESPONSE=$(curl --silent --request POST \
# --url https://${FUNCTION_ID}.invocation.api.nvcf.nvidia.com/bandwidth-test \
# --header "Authorization: Bearer ${KEY}" \
# --header 'NVCF-POLL-SECONDS: 300' \
# --header 'Content-Type: application/json' \
# --data '{
#   "bufferSize": 512,
#   "testSamples": 3,
#   "json": true
# }')
# 
# echo "$RESPONSE" | jq -r '.command'
# echo "$RESPONSE" | jq -r '.output'
# echo ""

echo "======================================================================================================"
echo " Test 2: Running device-to-device memcpy test"
echo "======================================================================================================"
RESPONSE=$(curl --silent --request POST \
--url https://${FUNCTION_ID}.invocation.api.nvcf.nvidia.com/bandwidth-test \
--header "Authorization: Bearer ${KEY}" \
--header 'NVCF-POLL-SECONDS: 300' \
--header 'Content-Type: application/json' \
--data '{
  "bufferSize": 256,
  "testcase": "device_to_device_memcpy_read_ce",
  "testSamples": 3,
  "json": true
}')

echo "$RESPONSE" | jq -r '.command'
echo "$RESPONSE" | jq -r '.output'
echo ""

echo "======================================================================================================"
echo " Test 3: Running host-to-device tests"
echo "======================================================================================================"
RESPONSE=$(curl --silent --request POST \
--url https://${FUNCTION_ID}.invocation.api.nvcf.nvidia.com/bandwidth-test \
--header "Authorization: Bearer ${KEY}" \
--header 'NVCF-POLL-SECONDS: 300' \
--header 'Content-Type: application/json' \
--data '{
  "bufferSize": 128,
  "testcasePrefix": "host_to_device",
  "testSamples": 2,
  "json": true
}')

echo "$RESPONSE" | jq -r '.command'
echo "$RESPONSE" | jq -r '.output'
echo ""

echo "======================================================================================================"
echo " Test 4: Running multinode bandwidth tests"
echo "======================================================================================================"
RESPONSE=$(curl --silent --request POST \
--url https://${FUNCTION_ID}.invocation.api.nvcf.nvidia.com/bandwidth-test \
--header "Authorization: Bearer ${KEY}" \
--header 'NVCF-POLL-SECONDS: 300' \
--header 'Content-Type: application/json' \
--data '{
  "bufferSize": 64,
  "testcasePrefix": "multinode",
  "testSamples": 3,
  "multinode": true,
  "np": 2,
  "json": true,
  "verbose": true
}')

echo "$RESPONSE" | jq -r '.command'
echo "$RESPONSE" | jq -r '.output'
echo ""

