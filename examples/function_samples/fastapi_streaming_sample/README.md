# FastAPI Sample
## Build the sample container
```bash
docker build . -t fastapi_streaming_sample
```
To upload it to NGC refer to [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry)

## Invoke the sample locally
```bash 
curl --request POST \
  --url localhost:8000/streaming_echo \
  --header 'Content-Type: application/json' \
  --data '{
  "message": "hello there"
}'
```

## Invoke the sample in NVCF
```bash 
curl --request POST \
  --url https://<function-id>.invocation.api.nvcf.nvidia.com/echo \
  --header 'Authorization: Bearer nvapi-<token>' \
  --header 'Content-Type: application/json' \
  --header 'Accept: text/event-stream' \
  --data '{
  "message": "hello there"
}'
```