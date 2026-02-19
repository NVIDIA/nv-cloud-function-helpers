# Examples

Sample containers for deploying functions and tasks on
[NVIDIA Cloud Functions (NVCF)](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/overview.html).

## Function Samples

Functions are long-running services that respond to HTTP or gRPC invocations.

| Sample | Description |
|--------|-------------|
| [FastAPI Echo](function_samples/fastapi_echo_sample/) | Minimal FastAPI function that echoes back the request payload. |
| [FastAPI Streaming](function_samples/fastapi_streaming_sample/) | FastAPI function demonstrating server-sent event (SSE) streaming responses. |
| [FastAPI Multi-Endpoint](function_samples/fastapi_multi_endpoint_sample/) | FastAPI function exposing multiple endpoints with query parameter support. |
| [gRPC Echo](function_samples/grpc_echo_sample/) | Echo function served via Triton Inference Server with an included Gradio client. |
| [Secrets](function_samples/secrets_sample/) | Shows how to read and use NVCF-managed secrets inside a container. |
| [vLLM OTLP Exporter](function_samples/vllm_otlp_exporter_sample/) | vLLM inference with OpenTelemetry (OTLP) metric exporting for BYO Observability. |
| [Inference Helm Chart](function_samples/helmchart_samples/inference_test_sample/) | Helm chart that deploys the FastAPI Echo sample on a Kubernetes cluster. |
| [Multi-Node Helm Function](function_samples/helmchart_samples/multi_node_helm_function_test/) | Multi-node Helm chart for running NCCL and GPU bandwidth tests via NVCF. |

## Task Samples

Tasks are short-lived, run-to-completion workloads (training jobs, batch processing, etc.).

| Sample | Description |
|--------|-------------|
| [Simple Task](tasks_samples/task_simple_sample/) | Minimal task container demonstrating progress reporting and result handling. |
| [Task with BYOO](tasks_samples/task_byoo_sample/) | Task container with Bring Your Own Observability (OpenTelemetry traces, metrics, and logs). |
| [Task Helm Chart](tasks_samples/task_helmchart_sample/) | Helm chart that deploys the simple task sample on a Kubernetes cluster. |
| [Task Helm Chart BYOO](tasks_samples/task_helmchart_byoo_sample/) | Helm chart that deploys the BYOO task sample on a Kubernetes cluster. |
| [Multi-Node Helm Task](tasks_samples/multi_node_helm_task_test/) | Multi-node Helm chart for running distributed task workloads. |

## Building for Multiple Compute Architectures

If both `amd64` and `arm64` support is required, Docker can build multi-platform images:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t my_image_name .
```

See the Docker [multi-platform build documentation](https://docs.docker.com/build/building/multi-platform/#cross-compilation) for more details.

## Uploading to NGC

After building a container, push it to the NGC Private Registry so it can be deployed as an NVCF function or task. Refer to the
[quickstart guide](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry)
for instructions.
