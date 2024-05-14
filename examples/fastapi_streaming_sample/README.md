# FastAPI Sample
## Build the sample container
```bash
docker build . -t fastapi_streaming_sample
```
To upload it to NGC refer to [here](https://developer.nvidia.com/docs/picasso/user-guide/latest/cloud-function/functions.html#preparing-your-container)

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
  --url https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/<function-id> \
  --header 'Authorization: Bearer nvapi-<token>' \
  --header 'Content-Type: application/json' \
  --header 'Accept: text/event-stream' \
  --data '{
  "message": "hello there"
}'
```