# Task Sample with Bring Your Own Observability (BYOO)

## Build the sample container
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t task_byoo_sample .
```
To upload it to NGC refer to [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry)

## Run sample locally
```bash
docker run -it -v ${PWD}:/tmp/output -e NVCT_RESULTS_DIR="/tmp/output" task_byoo_sample
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

## OpenTelemetry instrumentation

The sample supports `http` and `gRPC` protocols to send `oltp` signals (traces, metrics and logs). To define which protocol to use, run it with environment variable:

```
# for HTTP
export OTEL_EXPORTER_OTLP_${SIGNAL}_PROTOCOL=http

#for gRPC
export OTEL_EXPORTER_OTLP_${SIGNAL}_PROTOCOL=grpc
```

SIGNAL values are TRACES, LOGS and METRICS. gRPC is used by default if not is set.

The sample sends signals to console by default.

When running locally, the OTEL_* environment vars must be specified for the container run. Telemetry signals will only be sent the local `otlp` endpoint if they are specified. For NVCF deployments using BYO Observability feature the env vars for `otlp` are automatically populated as environment variables:
```
OTEL_EXPORTER_OTLP_${SIGNAL}_ENDPOINT
OTEL_EXPORTER_OTLP_${SIGNAL}_PROTOCOL
```

However, only the defined telemetry signal will be sent to the `otlp` endpoint.

SIGNAL values are TRACES, LOGS and METRICS.
