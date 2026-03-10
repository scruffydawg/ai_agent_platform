from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.logger import logger
import time
import asyncio
from typing import Dict

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = 0

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            self.last_failure_time = time.time()
            logger.error(f"CircuitBreaker: OPENED due to {self.failures} consecutive failures.")

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def can_proceed(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True

class ResilienceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.breakers: Dict[str, CircuitBreaker] = {
            "ollama": CircuitBreaker(),
            "search": CircuitBreaker()
        }

    async def dispatch(self, request: Request, call_next):
        # Identify external service endpoints (mock heuristic)
        path = request.url.path
        target = None
        if "/ollama" in path:
            target = "ollama"
        elif "/search" in path:
            target = "search"

        if target and target in self.breakers:
            if not self.breakers[target].can_proceed():
                logger.warning(f"ResilienceMiddleware: Blocking request to {target} (Circuit OPEN)")
                return Response(content=f"Service {target} is temporarily unavailable (Circuit Breaker)", status_code=503)

        start_time = time.time()
        try:
            response = await call_next(request)
            if target and response.status_code < 400:
                self.breakers[target].record_success()
            elif target and response.status_code >= 500:
                self.breakers[target].record_failure()
            return response
        except Exception as e:
            if target:
                self.breakers[target].record_failure()
            raise e
