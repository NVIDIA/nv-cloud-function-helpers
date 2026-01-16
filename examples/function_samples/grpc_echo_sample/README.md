# Echo Sample
This sample is a simple echo function served within a Triton Inference Server instance.

## Build the sample container
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t grpc_echo_sample .
```

To upload it to NGC refer to [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry)

## Run sample client application
Included with this sample is a client application that uses the function via an HTTP call. Run it using:
```bash
bash run_client_app.sh
```
A `gradio` base user interface will then be available at `localhost:7860`