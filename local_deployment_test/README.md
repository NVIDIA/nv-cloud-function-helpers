# Localhost Smoke Tests
A script with some verification steps to ensure a smooth deployment within NVCF.

## Setup
Please have installed [Docker](https://docs.docker.com/get-docker/) 
as well Python, alongside the package requirements outlined in `requirements.txt`
```bash
pip install -r requirements.txt
```

You will need a container prepared according to the [NVCF Documentation](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/overview.html).
You can find sample containers [here](https://gitlab-master.nvidia.com/kaizen/nvcf/nvcf-sample-function-containers).

## Running a compatibility check on a container

```bash
$python3 test_container.py --image_name test_container-baseline-inference-server --protocol http --health-endpoint v2/health/live --inference-endpoint /v2/models/echo/infer --container-port 8000
```