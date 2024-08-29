import os
import time
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, status
from fastapi.responses import StreamingResponse
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor as TracingInstrumentor,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.instrumentation.logging import LoggingInstrumentor

LoggingInstrumentor().instrument()

app = FastAPI()


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
    if echo.stream:

        def stream_text():
            for _ in range(echo.repeats):
                time.sleep(echo.delay)
                yield f"data: {echo.message}\n\n"

        return StreamingResponse(stream_text(), media_type="text/event-stream")
    else:
        time.sleep(echo.delay)
        return echo.message * echo.repeats


if __name__ == "__main__":
    resource = Resource(attributes={"service.name": "fastapi"})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter()
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    TracingInstrumentor.instrument_app(
        app, tracer_provider=provider, excluded_urls="health"
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)
