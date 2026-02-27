# Load Tester Supreme Sample
This sample provides both HTTP and gRPC echo servers designed for load and throughput testing.

Use `WORKER_COUNT` to control gRPC worker threads (default: `500`).

Request tuning fields:
- `message`: payload content
- `repeats`: number of response repeats
- `delay`: delay between responses in seconds

## Build the sample container
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t load_tester_supreme .
```

To upload it to NGC refer to [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry)

## Invoke the HTTP endpoint locally
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

## Invoke the streaming HTTP endpoint locally
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

## Invoke the gRPC endpoint locally
```bash
grpcurl -plaintext \
  -d '{"message":"hello","repeats":3,"delay":0.01}' \
  localhost:8001 Echo/EchoMessage
```