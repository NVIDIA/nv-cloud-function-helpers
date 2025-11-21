# NVCF Container Helpers
This repository contains examples, tests, and a library to ensure a smooth deployment within 
[NVIDIA Cloud Functions (NVCF)](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/overview.html).

## NVCF Container Helper Functions Library
The package `nvcf_container` provide Python functions that simplify common tasks within containers deployed inside  
[NVIDIA Cloud Functions](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/overview.html)

## Package Installation

```bash
pip3 install setuptools

pip3 install .
```

## Container Examples
The [examples/](./examples) folder has sample containers to be built and used as functions. 
They include a client app that interfaces with each function sample.

### Building for multiple compute architectures
If both `amd/64` and `arm/64` support is required, Docker can be used to support multi-platform images. 
Here is a sample command:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t my_image_name .
```

Please see additional reference material [here](https://docs.docker.com/build/building/multi-platform/#cross-compilation).
