# Load Tester Supreme

A dual-protocol echo server (HTTP + gRPC) purpose-built for load and throughput
testing of NVCF deployments. Use this instead of the simpler `grpc_echo_sample`
for any real load testing — it ships with 500 gRPC worker threads (vs 10) and
exposes tunable response behaviour.

## What's included

| Endpoint | Port | Description |
|----------|------|-------------|
| HTTP `/echo` | 8000 | JSON request/response and SSE streaming |
| HTTP `/health` | 8000 | Health check (returns 200) |
| HTTP `/ping-pong` | 8000 | Full-duplex HTTP/2 echo |
| gRPC `Echo/EchoMessage` | 8001 | Unary gRPC echo |
| gRPC `Echo/EchoMessageStreaming` | 8001 | Bidirectional streaming gRPC |

### Request tuning fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `message` | string | — | Payload content to echo back |
| `repeats` | int | 1 | Number of times to repeat the response |
| `delay` | float | ~0 | Seconds to sleep between responses |
| `size` | int | 0 | Generate a random string of this length instead of echoing `message` (HTTP only) |
| `stream` | bool | false | Return SSE stream instead of single response (HTTP only, requires `Accept: text/event-stream`) |

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKER_COUNT` | `500` | Number of gRPC server threads |

## Prerequisites

- Docker (with `buildx` for multi-platform builds)
- Access to a function container registry

## Build the container

```bash
cd examples/function_samples/load_tester_supreme

# Build for linux/amd64 (matches most cloud instances)
docker build --platform linux/amd64 -t load_tester_supreme .

# Or build multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t load_tester_supreme .
```

## Push to your registry

The image must be pushed to whatever container registry your NVCF cluster has
credentials for.

**NGC (nvcr.io):**

```bash
# Authenticate
echo "$NGC_API_KEY" | docker login nvcr.io -u '$oauthtoken' --password-stdin

# Tag and push
docker tag load_tester_supreme nvcr.io/<your-org>/load_tester_supreme:latest
docker push nvcr.io/<your-org>/load_tester_supreme:latest
```

## Test locally

Run the container:

```bash
docker run --rm -p 8000:8000 -p 8001:8001 load_tester_supreme
```

### HTTP

```bash
curl --request POST \
  --url localhost:8000/echo \
  --header 'Content-Type: application/json' \
  --data '{
  "message": "hello",
  "repeats": 3,
  "delay": 0.01
}'
```

### HTTP streaming

```bash
curl --request POST \
  --url localhost:8000/echo \
  --header 'Content-Type: application/json' \
  --header 'Accept: text/event-stream' \
  --data '{
  "message": "hello",
  "repeats": 5,
  "delay": 0.01,
  "stream": true
}'
```

### gRPC

```bash
grpcurl -plaintext \
  -d '{"message":"hello","repeats":3,"delay":0.01}' \
  localhost:8001 Echo/EchoMessage
```
