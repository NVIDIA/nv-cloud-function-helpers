# Task Helm Chart Sample
This sample is a helm chart deploying `task_simple_sample` container from NGC.

## Prerequisites

### Setup kubenetes cluster

To deploy helm chart, one needs to setup a kubenetes cluster locally. One recommendation is to use [microk8s](https://microk8s.io/docs/getting-started).

### Build and upload container image

For container build and upload details, please refer to [task_simple_sample](../task_simple_sample/README.md).


## Deploying

The sample helm chart will deploy a `task_simple_sample` container which will run until completion

First create a secret with your NGC API key

```
microk8s kubectl create secret docker-registry <image-pull-secret-name> --docker-server=nvcr.io --docker-username=$oauthtoken --docker-password=<NGC-API-KEY> 
```

Next deploy the sample helm chart with
```
microk8s helm install <release-name> /path/to/task-helmchart-test --set ngcImagePullSecretName=<image-pull-secret-name>
```
