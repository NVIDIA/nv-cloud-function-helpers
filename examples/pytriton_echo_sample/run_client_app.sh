#!/bin/bash

set -xe

docker build -f client/Dockerfile -t image_generation_sample_client_app .
docker run -it -p 7860:7860 image_generation_sample_client_app
