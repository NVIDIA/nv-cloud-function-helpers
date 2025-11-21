import os
import time
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, status
from fastapi.responses import StreamingResponse


app = FastAPI()


class HealthCheck(BaseModel):
    status: str = "OK"


@app.get("/health", tags=["healthcheck"], summary="Perform a Health Check", response_description="Return HTTP Status Code 200 (OK)", status_code=status.HTTP_200_OK, response_model=HealthCheck)
def get_health() -> HealthCheck:
    return HealthCheck(status="OK")


class StreamingEcho(BaseModel):
    message: str
    repeats: int = 1
    delay: float = 0.01


@app.post("/streaming_echo")
async def streaming(echo: StreamingEcho):
    word_list = echo.message.split(" ")

    def stream_text():
        for _ in range(echo.repeats):
            for word in word_list:
                time.sleep(echo.delay)
                yield f"data: {word}\n\n"

    return StreamingResponse(stream_text(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=int(os.getenv('WORKER_COUNT', 10)))
