# Echo Sample
This sample is a simple echo function served within a Triton Inference Server instance.

## Build the sample container
```bash
docker build . -t triton_echo_sample
```

To upload it to NGC refer to [here](https://developer.nvidia.com/docs/picasso/user-guide/latest/cloud-function/functions.html#preparing-your-container)


## Run sample client application
Included with this sample is a client application that uses the function via an HTTP call. Run it using:
```bash
bash run_client_app.sh
```
A `gradio` base user interface will then be available at `localhost:7860`