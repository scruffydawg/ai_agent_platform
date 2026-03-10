import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from apps.api.middleware.resilience_middleware import ResilienceMiddleware
from apps.api.middleware.rate_limit_middleware import RateLimitMiddleware

def register_middleware(app: FastAPI) -> None:
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    app.add_middleware(ResilienceMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # LAN-friendly
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["x-request-id"] = request_id
        response.headers["x-duration-ms"] = str(duration_ms)
        return response
