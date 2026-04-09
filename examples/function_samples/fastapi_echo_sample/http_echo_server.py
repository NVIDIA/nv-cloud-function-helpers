import hashlib
import os
import time
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import StreamingResponse


app = FastAPI()

class HealthCheck(BaseModel):
    status: str = "OK"

@app.get("/health", tags=["healthcheck"], summary="Perform a Health Check", response_description="Return HTTP Status Code 200 (OK)", status_code=status.HTTP_200_OK, response_model=HealthCheck)
def get_health() -> HealthCheck:
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
        return echo.message*echo.repeats

@app.post("/binary-echo")
async def binary_echo(request: Request):
    body = await request.body()
    md5 = hashlib.md5(body).hexdigest()
    return Response(
        content=body,
        media_type=request.headers.get("content-type", "application/octet-stream"),
        headers={
            "X-Echo-Size": str(len(body)),
            "X-Echo-MD5": md5,
            "X-Echo-Content-Type": request.headers.get("content-type", "application/octet-stream"),
        },
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=int(os.getenv('WORKER_COUNT', 500)))
