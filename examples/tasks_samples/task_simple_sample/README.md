# Tasks Sample
## Build the sample container
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t task_simple_sample .
```
To upload it to NGC refer to [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry)

## Run sample locally
```bash
docker run -it -v ${PWD}:/tmp/output -e NVCT_RESULTS_DIR="/tmp/output" task_simple_sample
```

## Progress file format

```
{
    "taskId": "579ad430-34b9-4a6e-9537-a060db4a9e6c"
    "percentComplete": 20,
    "name": "ckpt-step-2000",
    "metadata": 
    {
        "step-number": 2000,
        "token_accuracy": 0.874,
    },
    "lastUpdatedAt": "20025-01-02T15:04:05.999999999Z07:00"
}
```
- **taskId**: Task ID.
- **percentComplete**: Integer indicating the completion percentage between 1-100.
- **metadata**: Optional field for task container to add metadata regarding the upload. Required format: key-value pairs.
- **name**: Directory to upload to NGC. There are certain restrictions in naming the directory for UPLOAD strategy. The field should be 1-190 characters long. Allowed characters- [0-9a-zA-Z!-_.*’()]. Prefixes `./` and `../` are not allowed.
- **lastUpdatedAt**: ISO 8061 timestamp indicating when the progress file was last updated. Must be updated as minimum every 3 minutes to signal to NVCF the task is in progress.

## Deploy the Helm Chart Task
```bash
ngc cf task create \
  --org <> \
  --deployment-specification <gpu-name>:<instance> \
  --configuration '{
    "gpusPerNode": <num-gpus-per-node>,
    "nodesPerInstance": <number-of_nodes>,
    "image": {
      "repository": "nvcr.io/<org>/<name>",
      "pullPolicy": "Always",
      "tag": "<version>"
    }
  }' \
  --max-runtime-duration 1H \
  --max-queued-duration 1H \
  --termination-grace-period-duration 1H \
  --result-handling-strategy NONE
```