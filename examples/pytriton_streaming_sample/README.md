# Streaming Chatbot Sample
This sample is a simple echo function served within a PyTriton Inference Server instance.

## Build the sample container
```bash
docker build . -t triton_pytriton_streaming_dialogpt_sample
```

To upload it to NGC refer to [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry)


## Run sample client application
Included with this sample is a client application that uses the function via an HTTP call. Run it using:
```bash
bash run_client_app.sh
```
A `gradio` base user interface will then be available at `localhost:7860`

## Known problems 
The `streaming_client.py` is currently a CLI tool designed to interface with PyTriton directly. 
Future work needs to be done to make this a sample to interact with NVCF.