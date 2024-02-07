import logging
import os

import numpy as np
import time

from pytriton.decorators import batch
from pytriton.model_config import ModelConfig, Tensor
from pytriton.triton import Triton, TritonConfig

logger = logging.getLogger("sample.echo.server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s: %(message)s")


@batch
def _echo(**inputs):
    message = inputs["message"]
    if "response_delay_in_seconds" in inputs:
        response_delay_in_seconds = inputs["response_delay_in_seconds"]
    else:
        response_delay_in_seconds = 0.5

    time.sleep(float(response_delay_in_seconds))

    return {"echo": message}


with Triton(config=TritonConfig(
        allow_metrics=True,
        allow_gpu_metrics=True,
        allow_cpu_metrics=True,
        metrics_interval_ms=500,
        http_header_forward_pattern="(nvcf-.*|NVCF-.*)",
        strict_readiness=True,
        trace_config=[
            "mode=opentelemetry",
            "rate=1",
            "level=TIMESTAMPS",
            f"opentelemetry,resource=url={os.getenv('NVCF_TRACING_ENDPOINT_HTTP', 'http://localhost:4138/v1/traces')}",
        ],
        log_verbose=0)
) as triton:
    triton.bind(
        model_name="echo",
        infer_func=_echo,
        inputs=[
            Tensor(name="message", dtype=bytes, shape=[1]),
            Tensor(name="response_delay_in_seconds", dtype=np.float32, shape=[1], optional=True),
        ],
        outputs=[
            Tensor(name="echo", dtype=bytes, shape=[1]),
        ],
        config=ModelConfig(batching=False),
        strict=True,
    )
    logger.info("Serving model")
    triton.serve()
