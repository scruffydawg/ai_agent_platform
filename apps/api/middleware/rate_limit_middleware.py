from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.logger import logger
import time
from typing import Dict, Tuple

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_states: Dict[str, List[float]] = {} # ip -> timestamps

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        if client_ip not in self.client_states:
            self.client_states[client_ip] = []
            
        # Cleanup old timestamps (older than 1 minute)
        self.client_states[client_ip] = [t for t in self.client_states[client_ip] if current_time - t < 60]
        
        if len(self.client_states[client_ip]) >= self.requests_per_minute:
            logger.warning(f"RateLimitMiddleware: Blocking IP {client_ip} (Limit exceeded)")
            return Response(content="Rate limit exceeded. Try again in a minute.", status_code=429)
            
        self.client_states[client_ip].append(current_time)
        return await call_next(request)
