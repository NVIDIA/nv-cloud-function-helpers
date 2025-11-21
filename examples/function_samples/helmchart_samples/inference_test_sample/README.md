# Inference-test Sample
This sample is a helm chart deploying `fastapi_echo_sample` container from NGC.

## Prerequisites

### Setup kubenetes cluster

To deploy helm chart, one needs to setup a kubenetes cluster locally. One recommendation is to use [microk8s](https://microk8s.io/docs/getting-started).

### Build and upload container image

For container build and upload details, please refer to [fastapi_echo_sample](../../fastapi_echo_sample/README.md).


## Deploying

The sample helm chart will deploy a `fastapi_echo_sample` container and an `entrypoint` service for client communicating with the container.

First create a secret with your staging NGC API key

```
microk8s kubectl create secret docker-registry <image-pull-secret-name> --docker-server=stg.nvcr.io --docker-username=$oauthtoken --docker-password=<STG-NGC-API-KEY> 
```

Next deploy the sample helm chart with
```
microk8s helm install <release-name> /path/to/inference-test --set ngcImagePullSecretName=<image-pull-secret-name>
```


## Invoke the sample locally

Get cluster IP address of the `entrypoint` service through

```
microk8s kubectl get service entrypoint
```

Invoke deployed container by

```
curl --request POST \
  --url <entrypoint-service-ip>:8000/echo \
  --header 'Content-Type: application/json' \
  --data '{
  "message": "hello"
}'
```

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