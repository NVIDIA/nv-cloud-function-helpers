import os
import time
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, status
from fastapi.responses import StreamingResponse
import requests
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import get_meter_provider, set_meter_provider


app = FastAPI()

class HealthCheck(BaseModel):
    status: str = "OK"

@app.get("/health", tags=["healthcheck"], summary="Perform a Health Check", response_description="Return HTTP Status Code 200 (OK)", status_code=status.HTTP_200_OK, response_model=HealthCheck)
def get_health() -> HealthCheck:
    return HealthCheck(status="OK")

class Echo(BaseModel):
    message: str = ""
    delay: float = 0.000001
    repeats: int = 1
    stream: bool = False
    url: str = ""


@app.post("/echo")
async def echo(echo: Echo):
    echo_requests_total.add(1)
    active_connections.inc()
    
    if echo.url:
        try:
            response = requests.get(echo.url)
            s = f"""
                code: {response.status_code}
                text: {response.text}
                
            """
            return s
        except requests.exceptions.RequestException as e:
            return str(e)
        except requests.exceptions.HTTPError as e:
            return str(e)
        except requests.exceptions.ConnectionError as e:
            return str(e)
        except requests.exceptions.Timeout as e:
            return str(e)
        except requests.exceptions.RequestException as e:
            return str(e)
    elif echo.stream:
        def stream_text():
            for _ in range(echo.repeats):
                time.sleep(echo.delay)
                yield f"data: {echo.message}\n\n"
        return StreamingResponse(stream_text(), media_type="text/event-stream")
    else:
        start = time.time()
        time.sleep(echo.delay)
        result = echo.message*echo.repeats
        response_time.observe(time.time() - start)
        active_connections.dec()
        return result


def init_observability():
    global echo_requests_total
    resource = Resource(attributes={"service.name": os.getenv("OTEL_SERVICE_NAME", "http-echo")})
    metric_exporter = OTLPMetricExporter()
    reader = PeriodicExportingMetricReader(
        metric_exporter, export_interval_millis=60_000
    )
    meter_provider = MeterProvider(metric_readers=[reader], resource=resource)
    set_meter_provider(meter_provider)
    meter = get_meter_provider().get_meter("my_meeter")
    echo_requests_total = meter.create_counter(
        "echo_requests_total", "counter", "Total number of echo requests"
    )


if __name__ == "__main__":
    init_observability()
    uvicorn.run(app, host="0.0.0.0", port=8000)
