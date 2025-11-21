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

RESPONSE=$(curl --silent --request POST \
--url https://${FUNCTION_ID}.invocation.api.nvcf.nvidia.com/nccl-test \
--header "Authorization: Bearer ${KEY}" \
--header "NVCF-POLL-SECONDS: 300" \
--header 'Content-Type: application/json' \
--data '{
  "np": 8,
  "n": "20",
  "b": "1K",
  "e": "16G",
  "f": "2",
  "g": "1",
  "npernode": 4,
  "mnnvl": true,
  "debug": true
}')

# echo "$RESPONSE"

echo ""
echo "======================================================================================================"
echo " NCCL Test Output"
echo "======================================================================================================"
echo "$RESPONSE" | jq -r '.command'
echo "$RESPONSE" | jq -r '.output'
echo ""
echo "======================================================================================================"

# save the formatted response to a file
echo "$RESPONSE" | jq -r '.command' > nccl_test_response.json
echo "$RESPONSE" | jq -r '.output' >> nccl_test_response.json