# FastAPI Echo Sample

A lightweight FastAPI container with three endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (returns `{"status": "OK"}`) |
| `/echo` | POST | JSON echo with optional streaming and repeat |
| `/binary-echo` | POST | Binary pass-through -- returns the raw request body with integrity metadata headers |

## Build

```bash
docker build . -t fastapi_echo_sample:latest
```

For cross-platform builds (e.g., building on Apple Silicon for an x86 cluster):

```bash
docker buildx build --platform linux/amd64 -t fastapi_echo_sample:latest .
```

## Push to NGC

```bash
docker tag fastapi_echo_sample:latest nvcr.io/<org-id>/fastapi_echo_sample:<tag>
docker push nvcr.io/<org-id>/fastapi_echo_sample:<tag>
```

See the [NGC container registry docs](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry) for authentication details.

## Test locally

```bash
docker run --rm -p 8000:8000 fastapi_echo_sample:latest
```

JSON echo:

```bash
curl -X POST http://localhost:8000/echo \
  -H 'Content-Type: application/json' \
  -d '{"message": "hello"}'
```

Binary echo:

```bash
echo "hello world" | curl -X POST http://localhost:8000/binary-echo \
  -H 'Content-Type: application/octet-stream' \
  --data-binary @- -v
```

## Deploy to NVCF

### Step 1: Create the function

```bash
curl -s -X POST 'https://api.ngc.nvidia.com/v2/nvcf/functions' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "name": "fastapi-echo",
    "inferenceUrl": "/echo",
    "inferencePort": 8000,
    "containerImage": "nvcr.io/<org-id>/fastapi_echo_sample:<tag>",
    "apiBodyFormat": "CUSTOM",
    "health": {
      "protocol": "HTTP",
      "uri": "/health",
      "port": 8000,
      "timeout": "PT30S",
      "expectedStatusCode": 200
    }
  }'
```

Save the `id` (function ID) and `versionId` from the response.

### Step 2: Deploy

```bash
curl -s -X POST "https://api.ngc.nvidia.com/v2/nvcf/deployments/functions/$FUNCTION_ID/versions/$VERSION_ID" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "deploymentSpecifications": [
      {
        "gpu": "<gpu-type>",
        "instanceType": "<instance-type>",
        "backend": "<cluster-group-name>",
        "minInstances": 1,
        "maxInstances": 1,
        "maxRequestConcurrency": 1
      }
    ]
  }'
```

Replace `<gpu-type>`, `<instance-type>`, and `<cluster-group-name>` with values
from your cluster group (see `GET /v2/nvcf/clusterGroups`).

### Step 3: Wait for ACTIVE status

```bash
curl -s "https://api.ngc.nvidia.com/v2/nvcf/functions/$FUNCTION_ID/versions/$VERSION_ID" \
  -H "Authorization: Bearer $API_KEY" | jq '.function.status'
```

## Invoke via direct invocation

Once the function is ACTIVE, call it through the direct invocation endpoint.
This bypasses the legacy `/pexec` path -- no Protobuf wrapping, no size limits,
native streaming.

JSON echo:

```bash
curl -X POST "https://${FUNCTION_ID}.invocation.api.nvcf.nvidia.com/echo" \
  -H "Authorization: Bearer $API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"message": "hello", "repeats": 3}'
```

Binary echo:

```bash
curl -X POST "https://${FUNCTION_ID}.invocation.api.nvcf.nvidia.com/binary-echo" \
  -H "Authorization: Bearer $API_KEY" \
  -H 'Content-Type: application/octet-stream' \
  --data-binary @my-file.bin -v
```

The response body is the same bytes you sent. Check the response headers for
integrity metadata:

- `X-Echo-Size` -- byte count
- `X-Echo-MD5` -- MD5 hex digest
- `X-Echo-Content-Type` -- echoed content type

## Large binary streaming test

`test-binary-streaming.sh` validates that large payloads round-trip correctly
through direct invocation. It generates random payloads at 50KB, 1MB, 10MB, and
50MB, sends each to `/binary-echo`, and compares MD5 checksums.

```bash
FUNCTION_ID="<function-id>" API_KEY="nvapi-<token>" ./test-binary-streaming.sh
```

Example output:

```
TEST      HTTP    LATENCY     SENT MD5                            RECV MD5                            RESULT
--------------------------------------------------------------------------------------------------------------
50KB      200        1028ms  b4f4b4712d7d32fdf8db1103cc671345    b4f4b4712d7d32fdf8db1103cc671345    PASS
1MB       200        2204ms  0370b8d28bb874a9feb20574b4bc2709    0370b8d28bb874a9feb20574b4bc2709    PASS
10MB      200        2891ms  b80bf7b726b4e818aa27884c572424c9    b80bf7b726b4e818aa27884c572424c9    PASS
50MB      200       10066ms  eb43f17ff00461d08488fe4dffc55f55    eb43f17ff00461d08488fe4dffc55f55    PASS
--------------------------------------------------------------------------------------------------------------
Results: 4 passed, 0 failed
```
