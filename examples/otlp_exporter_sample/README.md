# OpenTelemetry Instrumentation

This is a function built for testing [OpenTelemetry](https://opentelemetry.io/) instrumentation for metrics, traces and logs. The echo http python server (`fastapi_echo_sample`) is used as example in instrumentation three flavors:
* automatic: zero code instrumentation, where the instrumentation is done by the `opentelemetry-bootstrap -a install`. It will install instrumentation libraries for the application packages. More details in [here](https://opentelemetry.io/docs/zero-code/python/).
* programmatic: auto instrumentation will automate OpenTelemetry instrumentation for packages it knows and some manual instrumentation is used to focus or improve the auto instrumentation.
* manual: one uses the OpenTelemetry SDK to instrument parts of the application code where traces, metrics and logs should be created. More details in [here](https://opentelemetry.io/docs/languages/python/instrumentation/).

The number of workers of each can be controlled with the environment variable `WORKER_COUNT`.

Additionally to the python code instrumentation the container also includes [`node_exporter`](https://github.com/prometheus/node_exporter) and [`DCGM exporter`](https://github.com/NVIDIA/dcgm-exporter) for node and GPU metrics. Refer to the provided linkis for details on how to use and configuration of those exporters.

## Build the sample containers
Each of the sample containers have environment variables that must be configure to define where traces, logs and metrics should be exported to.

Documentation from OpenTelemetry on environment variables [here](https://opentelemetry.io/docs/languages/sdk-configuration/otlp-exporter/).
```
ENV OTEL_TRACES_EXPORTER="console,otlp"
ENV OTEL_LOGS_EXPORTER="console"
ENV OTEL_METRICS_EXPORTER="console,otlp"
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
ENV OTEL_SERVICE_NAME="echo_manual"
# add configuration for a local otel collector or NVCF_TRACING_ENDPOINT_HTTP
ENV OTEL_EXPORTER_OTLP_ENDPOINT="localhost:4317"
```

By default console and `otlp` are used for programmatic and auto instrumentation versions. For manual instrumentation, `otlp` is used for traces and metrics, while console is used for logs.

### Local build and run

Before building the containers, one need to set the env variables that sets the Grafana Cloud endpoint for the otel collector configuration. The below environment variables will be required:

```
export GrafanaEndpoint=<>
export GrafanaInstanceID=<>
export GrafanaCloudToken=<>
```

```bash
docker build -t echo-manual:latest -f Dockerfile_manual .
docker build -t echo-automatic:latest -f Dockerfile_manual .
docker build -t echo-programmatic:latest -f Dockerfile_programmatic .
```

Locally one can run and test the above container as follow:
```
docker run -it -p 8000:8000 echo-manual:latest

# test
curl -X POST localhost:8000/echo  -H 'Content-Type: application/json'  --data '{"message": "hello"}'
```

The above should produce in the console something as below:

<details>
  <summary>Click me - output</summary>

```
{
    "body": "echo request: hello",
    "severity_number": "<SeverityNumber.WARN: 13>",
    "severity_text": "WARN",
    "attributes": {
        "code.filepath": "/app/http_echo_server_manual.py",
        "code.function": "echo",
        "code.lineno": 115
    },
    "dropped_attributes": 0,
    "timestamp": "2024-07-10T13:08:19.432697Z",
    "observed_timestamp": "2024-07-10T13:08:19.432758Z",
    "trace_id": "0xfc53aaef3b145b9fcbf0abc6da33e7eb",
    "span_id": "0x25ca4c129b2c0991",
    "trace_flags": 1,
    "resource": "{'service.name': 'fastapi'}"
}

{
    "resource_metrics": [
        {
            "resource": {
                "attributes": {
                    "telemetry.sdk.language": "python",
                    "telemetry.sdk.name": "opentelemetry",
                    "telemetry.sdk.version": "1.23.0",
                    "telemetry.auto.version": "0.44b0",
                    "service.name": "unknown_service"
                },
                "schema_url": ""
            },
            "scope_metrics": [
                {
                    "scope": {
                        "name": "opentelemetry.instrumentation.fastapi",
                        "version": "0.44b0",
                        "schema_url": "https://opentelemetry.io/schemas/1.11.0"
                    },
                    "metrics": [
                        {
                            "name": "http.server.active_requests",
                            "description": "measures the number of concurrent HTTP requests that are currently in-flight",
                            "unit": "requests",
                            "data": {
                                "data_points": [
                                    {
                                        "attributes": {
                                            "http.method": "POST",
                                            "http.scheme": "http",
                                            "http.host": "127.0.0.1:8000",
                                            "http.server_name": "0.0.0.0:8000",
                                            "http.flavor": "1.1"
                                        },
                                        "start_time_unix_nano": 1720620546994981479,
                                        "time_unix_nano": 1720620585565855320,
                                        "value": 0
                                    }
                                ],
                                "aggregation_temporality": 2,
                                "is_monotonic": false
                            }
                        },
                        {
                            "name": "http.server.duration",
                            "description": "measures the duration of the inbound HTTP request",
                            "unit": "ms",
                            "data": {
                                "data_points": [
                                    {
                                        "attributes": {
                                            "http.method": "POST",
                                            "http.scheme": "http",
                                            "http.host": "127.0.0.1:8000",
                                            "http.server_name": "0.0.0.0:8000",
                                            "net.host.port": 8000,
                                            "http.flavor": "1.1",
                                            "http.status_code": 200,
                                            "http.target": "/echo"
                                        },
                                        "start_time_unix_nano": 1720620546996499733,
                                        "time_unix_nano": 1720620585565855320,
                                        "count": 1,
                                        "sum": 2,
                                        "bucket_counts": [
                                            0,
                                            1,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0
                                        ],
                                        "explicit_bounds": [
                                            0.0,
                                            5.0,
                                            10.0,
                                            25.0,
                                            50.0,
                                            75.0,
                                            100.0,
                                            250.0,
                                            500.0,
                                            750.0,
                                            1000.0,
                                            2500.0,
                                            5000.0,
                                            7500.0,
                                            10000.0
                                        ],
                                        "min": 2,
                                        "max": 2
                                    }
                                ],
                                "aggregation_temporality": 2
                            }
                        },
                        {
                            "name": "http.server.response.size",
                            "description": "measures the size of HTTP response messages (compressed).",
                            "unit": "By",
                            "data": {
                                "data_points": [
                                    {
                                        "attributes": {
                                            "http.method": "POST",
                                            "http.scheme": "http",
                                            "http.host": "127.0.0.1:8000",
                                            "http.server_name": "0.0.0.0:8000",
                                            "net.host.port": 8000,
                                            "http.flavor": "1.1",
                                            "http.status_code": 200,
                                            "http.target": "/echo"
                                        },
                                        "start_time_unix_nano": 1720620546996662216,
                                        "time_unix_nano": 1720620585565855320,
                                        "count": 1,
                                        "sum": 7,
                                        "bucket_counts": [
                                            0,
                                            0,
                                            1,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0
                                        ],
                                        "explicit_bounds": [
                                            0.0,
                                            5.0,
                                            10.0,
                                            25.0,
                                            50.0,
                                            75.0,
                                            100.0,
                                            250.0,
                                            500.0,
                                            750.0,
                                            1000.0,
                                            2500.0,
                                            5000.0,
                                            7500.0,
                                            10000.0
                                        ],
                                        "min": 7,
                                        "max": 7
                                    }
                                ],
                                "aggregation_temporality": 2
                            }
                        },
                        {
                            "name": "http.server.request.size",
                            "description": "Measures the size of HTTP request messages (compressed).",
                            "unit": "By",
                            "data": {
                                "data_points": [
                                    {
                                        "attributes": {
                                            "http.method": "POST",
                                            "http.scheme": "http",
                                            "http.host": "127.0.0.1:8000",
                                            "http.server_name": "0.0.0.0:8000",
                                            "net.host.port": 8000,
                                            "http.flavor": "1.1",
                                            "http.status_code": 200,
                                            "http.target": "/echo"
                                        },
                                        "start_time_unix_nano": 1720620546996692072,
                                        "time_unix_nano": 1720620585565855320,
                                        "count": 1,
                                        "sum": 20,
                                        "bucket_counts": [
                                            0,
                                            0,
                                            0,
                                            1,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0
                                        ],
                                        "explicit_bounds": [
                                            0.0,
                                            5.0,
                                            10.0,
                                            25.0,
                                            50.0,
                                            75.0,
                                            100.0,
                                            250.0,
                                            500.0,
                                            750.0,
                                            1000.0,
                                            2500.0,
                                            5000.0,
                                            7500.0,
                                            10000.0
                                        ],
                                        "min": 20,
                                        "max": 20
                                    }
                                ],
                                "aggregation_temporality": 2
                            }
                        }
                    ],
                    "schema_url": "https://opentelemetry.io/schemas/1.11.0"
                }
            ],
            "schema_url": ""
        }
    ]
}

# no collector running, will also generate
{
    "body": "Failed to export traces to , error code: StatusCode.UNKNOWN",
    "severity_number": "<SeverityNumber.ERROR: 17>",
    "severity_text": "ERROR",
    "attributes": {
        "code.filepath": "/usr/local/lib/python3.10/site-packages/opentelemetry/exporter/otlp/proto/grpc/exporter.py",
        "code.function": "_export",
        "code.lineno": 306,
        "exception.type": "_InactiveRpcError",
        "exception.stacktrace": "Traceback (most recent call last):\n  File \"/usr/local/lib/python3.10/site-packages/opentelemetry/exporter/otlp/proto/grpc/exporter.py\", line 262, in _export\n    self._client.Export(\n  File \"/usr/local/lib/python3.10/site-packages/grpc/_channel.py\", line 1161, in __call__\n    return _end_unary_response_blocking(state, call, False, None)\n  File \"/usr/local/lib/python3.10/site-packages/grpc/_channel.py\", line 1004, in _end_unary_response_blocking\n    raise _InactiveRpcError(state)  # pytype: disable=not-instantiable\ngrpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:\n\tstatus = StatusCode.UNKNOWN\n\tdetails = \"Failed to create secure client channel\"\n\tdebug_error_string = \"UNKNOWN:Failed to create secure client channel {grpc_status:2}\"\n>\n"
    },
    "dropped_attributes": 0,
    "timestamp": "2024-07-10T13:08:24.286991Z",
    "observed_timestamp": "2024-07-10T13:08:24.287030Z",
    "trace_id": "0x00000000000000000000000000000000",
    "span_id": "0x0000000000000000",
    "trace_flags": 0,
    "resource": "{'service.name': 'fastapi'}"
}
```
</details>

### NVCF build and run

Before building the example container image you need to setup the Grafana Cloud OTLP endpoint, which will be used in the collector configuration file (environment variable `GrafanaEndpoint`). Please refer to https://grafana.com/docs/grafana-cloud/send-data/otlp/send-data-otlp/ to setup it.

To build the automatic instrumentation of `fastapi_echo_sample` example for NVCF use the below command. Note this is an instrumented version of the `fastapi_echo_sample` from other provided samples.

```bash
docker build -t nvcr.io/YOUR_ORG/echo-auto:latest . -f Dockerfile_automatic
```

To upload the container image to NGC refer to [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#clone-build-and-push-the-docker-image-to-ngc-private-registry).

Once the container image is uploaded to NGC, the creation and deployment of the NVCF container function can be done. Refer to the NVCF [quickstart](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/quickstart.html#create-deploy-the-function-using-the-cloud-functions-ui) for this.

Please notice that the Grafana environment variables must be set when deploying the function so that the OpenTelemetry collector configuration can use them, see [config](./otel-collector-config.yaml).

A deployed function for the `http_echo_server_manual.py` example has the below info:

<details>
  <summary>Click me - output</summary>

```
ngc cf function info --format_type json FUNCTION_ID:FUNCTION_VERSION_ID
{
    "apiBodyFormat": "CUSTOM",
    "containerEnvironment": [
        {
            "key": "GrafanaInstanceID",
            "value": "XXXXX"
        },
        {
            "key": "GrafanaCloudToken",
            "value": "XXXXXXX"
        },
        {
            "key": "endpoint",
            "value": "https://XXXXXX.grafana.net/otlp"
        }
    ],
    "containerImage": "nvcr.io/YOUR_ORG/echo-manual:latest",
    "functionType": "DEFAULT",
    "health": {
        "expectedStatusCode": 200,
        "port": 8000,
        "protocol": "HTTP",
        "timeout": "PT10S",
        "uri": "/health"
    },
    "healthUri": "/health",
    "inferencePort": 8000,
    "inferenceUrl": "/echo",
    "name": "YOUR_FUNCTION_NAME",
    "ncaId": "YOUR_ORG_NCA_ID",
    ....
}
```
</details>