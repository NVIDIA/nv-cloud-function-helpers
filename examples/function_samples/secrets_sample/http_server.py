import os
import json
import logging
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

SECRETS_PATH = os.getenv("SECRETS_PATH", "/var/secrets/secrets.json")
ACCOUNTS_SECRETS_PATH = os.getenv("ACCOUNTS_SECRETS_PATH", "/var/secrets/accounts-secrets.json")

class HealthCheck(BaseModel):
    status: str = "OK"


@app.get("/health", tags=["healthcheck"], summary="Perform a Health Check",
         response_description="Return HTTP Status Code 200 (OK)", status_code=status.HTTP_200_OK,
         response_model=HealthCheck)
def get_health() -> HealthCheck:
    return HealthCheck(status="OK")


class SecretRequest(BaseModel):
    key: str = ""


@app.post("/test")
async def get_secrets(sr: SecretRequest):
    func_secrets = get_secret_from_path(SECRETS_PATH, sr.key)
    acct_secrets = get_secret_from_path(ACCOUNTS_SECRETS_PATH, sr.key)
    return {"function secrets": func_secrets, "account secrets": acct_secrets}

def get_secret_from_path(path, key: str):
    try:
        with open(path) as f:
            content = f.read()
            if not content or content.strip() == "":
                logger.warning(f"Secret file at {path} is empty")
                return {}
            
            secrets = json.loads(content)
            if key != "":
                if key in secrets:
                    return {key: secrets[key]}
                else:
                    logger.warning(f"Key '{key}' not found in secrets at {path}")
                    return {}
            else:
                return secrets
    except FileNotFoundError:
        logger.error(f"Secret file not found at {path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in secret file at {path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error reading secrets from {path}: {e}")
        return {}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=int(os.getenv('WORKER_COUNT', 1)))
