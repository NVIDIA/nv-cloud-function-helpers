import os
import time
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, status
from fastapi.responses import StreamingResponse
import requests


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
        time.sleep(echo.delay)
        return echo.message*echo.repeats

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=int(os.getenv('WORKER_COUNT', 500)))
