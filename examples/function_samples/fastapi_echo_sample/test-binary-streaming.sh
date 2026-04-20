#!/usr/bin/env bash
# test-binary-streaming.sh -- validate large binary payloads via direct invocation
#
# Required env vars:
#   FUNCTION_ID  -- the NVCF function ID
#   API_KEY      -- NGC API key (nvapi-...)
#
# Usage:
#   FUNCTION_ID="abc-123" API_KEY="nvapi-..." ./test-binary-streaming.sh

set -euo pipefail

: "${FUNCTION_ID:?Set FUNCTION_ID}"
: "${API_KEY:?Set API_KEY}"

BASE_URL="https://${FUNCTION_ID}.invocation.api.nvcf.nvidia.com"
TMPDIR_BASE=$(mktemp -d)
trap 'rm -rf "$TMPDIR_BASE"' EXIT

# ---------- helpers ----------

generate_payload() {
    local size_bytes=$1 path=$2
    dd if=/dev/urandom of="$path" bs=1024 count=$((size_bytes / 1024)) 2>/dev/null
}

md5_of() {
    md5 -q "$1" 2>/dev/null || md5sum "$1" | awk '{print $1}'
}

# ---------- test matrix ----------

declare -a NAMES=("50KB" "1MB" "10MB" "50MB")
declare -a SIZES=(51200 1048576 10485760 52428800)

PASS=0
FAIL=0

printf "\n%-8s  %-6s  %-10s  %-34s  %-34s  %s\n" \
    "TEST" "HTTP" "LATENCY" "SENT MD5" "RECV MD5" "RESULT"
printf '%0.s-' {1..110}; echo

for i in "${!NAMES[@]}"; do
    name="${NAMES[$i]}"
    size="${SIZES[$i]}"
    payload="$TMPDIR_BASE/payload-${name}"

    generate_payload "$size" "$payload"
    sent_md5=$(md5_of "$payload")

    resp_file="$TMPDIR_BASE/resp-${name}"
    header_file="$TMPDIR_BASE/headers-${name}"

    start=$(python3 -c 'import time; print(int(time.time()*1000))')

    http_code=$(curl -s -o "$resp_file" -D "$header_file" -w "%{http_code}" \
        -X POST "${BASE_URL}/binary-echo" \
        -H "Authorization: Bearer ${API_KEY}" \
        -H "Content-Type: application/octet-stream" \
        --data-binary @"$payload" \
        --max-time 300)

    end=$(python3 -c 'import time; print(int(time.time()*1000))')
    latency=$(( end - start ))

    recv_md5=$(md5_of "$resp_file")

    if [[ "$http_code" == "200" && "$sent_md5" == "$recv_md5" ]]; then
        result="PASS"
        ((PASS++))
    else
        result="FAIL"
        ((FAIL++))
    fi

    printf "%-8s  %-6s  %7dms  %-34s  %-34s  %s\n" \
        "$name" "$http_code" "$latency" "$sent_md5" "$recv_md5" "$result"
done

printf '%0.s-' {1..110}; echo
printf "Results: %d passed, %d failed\n\n" "$PASS" "$FAIL"

if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi
