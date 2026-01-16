# FastAPI Multi-Endpoint Sample
## Build the sample container
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t fastapi_multi_endpoint_sample .
```
To upload it to NGC refer to [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry)

## Invoke the sample locally
```bash 
curl --request POST \
  --url localhost:8000/echo \
  --header 'Content-Type: application/json' \
  --data '{
  "message": "hello"
}'
```

## Invoke the sample in NVCF
You can use the function id as part of the url, or the function id and version id as a header

```bash 
curl --request POST \
  --url https://<function-id>.invocation.api.nvcf.nvidia.com/echo \
  --header 'Authorization: Bearer nvapi-<token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "message": "hello"
}'
```

or use (NOTE: This is an experimental feature!)

```bash 
curl --request POST \
  --url https://invocation.api.nvcf.nvidia.com/echo \
  --header 'function-id: <function-id>' \
  --header 'function-version-id: <version-id>' \
  --header 'Authorization: Bearer nvapi-<token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "message": "hello"
}'
```

Also we can use query parameters as part of the request
```bash 
curl --request POST \
  --url https://<function-id>.invocation.api.nvcf.nvidia.com/echo?name=John \
  --header 'Authorization: Bearer nvapi-<token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "name": "John", 
}'
```