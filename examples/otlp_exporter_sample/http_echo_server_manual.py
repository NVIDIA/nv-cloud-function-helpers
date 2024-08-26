import os
import time
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, status
from fastapi.responses import StreamingResponse


# otlp traces
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# logs
import logging
from opentelemetry.sdk._logs.export import (
    SimpleLogRecordProcessor,
    ConsoleLogExporter,
)
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry._logs import set_logger_provider, get_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

# otlp metrics
from opentelemetry import metrics
from opentelemetry.metrics import get_meter_provider, set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

app = FastAPI()

# app metric
echo_requests_total = None
# tracer for app traces/spans
tracer = None
# log handler
handler = None


def init_observability():
    global echo_requests_total, tracer, handler
    resource = Resource(attributes={"service.name": "echo-manual"})
    tracer_provider = TracerProvider(resource=resource)

    trace_exporter = OTLPSpanExporter()
    processor = BatchSpanProcessor(trace_exporter)
    tracer_provider.add_span_processor(processor)
    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer_provider().get_tracer(__name__)

    logger_provider = LoggerProvider(resource=resource)
    log_exporter = OTLPLogExporter(insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

    metric_exporter = OTLPMetricExporter()
    reader = PeriodicExportingMetricReader(
        metric_exporter, export_interval_millis=60_000
    )
    meter_provider = MeterProvider(metric_readers=[reader])
    set_meter_provider(meter_provider)
    meter = get_meter_provider().get_meter("my_meeter")
    echo_requests_total = meter.create_counter(
        "echo_requests_total", "counter", "Total number of echo requests"
    )


init_observability()
logging.getLogger().addHandler(handler)


class HealthCheck(BaseModel):
    status: str = "OK"


@app.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health() -> HealthCheck:
    """
    Endpoint to perform a health check. This endpoint can primarily be used by Docker
    to ensure robust container orchestration and management is in place. Other
    services which rely on the proper functioning of the API service will not deploy
    if this endpoint returns any other HTTP status code except 200 (OK).

    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")


class Echo(BaseModel):
    message: str
    delay: float = 0.000001
    repeats: int = 1
    stream: bool = False


@app.post("/echo")
async def echo(echo: Echo):
    with tracer.start_as_current_span("echo") as span:
        logging.warning("echo request: %s", echo.message)
        span.set_attribute("http.method", "POST")
        if echo.stream:
            echo_requests_total.add(1, attributes={"http.method": "POST"})
            get_logger_provider().get_logger("my_stream").emit("echo", echo)

            def stream_text():
                for _ in range(echo.repeats):
                    time.sleep(echo.delay)
                    yield f"data: {echo.message}\n\n"

            return StreamingResponse(stream_text(), media_type="text/event-stream")
        else:
            time.sleep(echo.delay)
            return echo.message * echo.repeats


if __name__ == "__main__":
    uvicorn.run(
        app, host="0.0.0.0", port=8000, workers=int(os.getenv("WORKER_COUNT", 5))
    )
