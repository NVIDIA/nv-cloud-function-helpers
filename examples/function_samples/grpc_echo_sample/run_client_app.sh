#!/bin/bash

set -xe

docker buildx build --platform linux/amd64,linux/arm64 -f client/Dockerfile -t image_generation_sample_client_app .
docker run -it -p 7860:7860 image_generation_sample_client_app
