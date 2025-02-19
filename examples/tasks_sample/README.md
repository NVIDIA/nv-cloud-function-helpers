# Tasks Sample
## Build the sample container
```bash
docker build . -t tasks_sample
```
To upload it to NGC refer to [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry)

## Run sample locally
```bash
docker run -it -v ${PWD}:/tmp/output -e NVCT_RESULTS_DIR="/tmp/output" tasks_sample
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
    }
}
```
- **taskId**: Task ID.
- **percentComplete**: Integer indicating the completion percentage between 1-100.
- **metadata**: Optional field for task container to add metadata regarding the upload. Required format: key-value pairs.
- **name**: Directory to upload to NGC. There are certain restrictions in naming the directory for UPLOAD strategy. The field should be 1-190 characters long. Allowed characters- [0-9a-zA-Z!-_.*’()]. Prefixes `./` and `../` are not allowed.