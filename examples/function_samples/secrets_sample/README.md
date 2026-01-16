# Secrets Sample
## Build the sample container
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t secrets_sample .
```
To upload it to NGC refer to [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry)

## Invoke the sample locally
Run the container:
```bash 
docker run -it -p 8000:8000 -v ${PWD}/secret_sample:/var/secrets secrets_sample
```

Then invoke to retrieve a specific secret:

```bash 
curl --request POST \
  --url localhost:8000/test \
  --header 'Content-Type: application/json' \
  --data '{
  "key": "secret-key-1"
}'
```

Or retrieve all secrets with a blank request:

```bash 
curl --request POST \
  --url localhost:8000/test \
  --header 'Content-Type: application/json' \
  --data '{}'
```

### Error Handling
The server gracefully handles missing or empty secret files by:
- Returning an empty dictionary for missing/empty files
- Logging errors to help with debugging
- Continuing to serve requests without crashing

If a secret file is not found or empty, you'll see log entries like:
```
ERROR:http_server:Secret file not found at /var/secrets/accounts-secrets.json
```

The API will still return a 200 OK response with empty dictionaries for any missing secrets.

## Invoke the sample in NVCF
```bash 
curl --request POST \
  --url https://<function-id>.invocation.api.nvcf.nvidia.com/test
  --header 'Authorization: Bearer nvapi-<token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "key": "secret-key-1"
}'
```