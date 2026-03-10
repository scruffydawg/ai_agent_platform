import time
from typing import Dict, Any
from src.utils.logger import logger
from packages.services.event_service import event_service

class MetricsService:
    def __init__(self):
        self.metrics = {
            "request_count": 0,
            "total_latency": 0.0,
            "token_usage": 0,
            "errors": 0
        }

    async def record_request(self, latency: float, tokens: int = 0, success: bool = True):
        self.metrics["request_count"] += 1
        self.metrics["total_latency"] += latency
        self.metrics["token_usage"] += tokens
        if not success:
            self.metrics["errors"] += 1
            
        # Publish metrics event for live dashboarding
        await event_service.publish({
            "type": "METRICS_UPDATE",
            "payload": {
                "latency": latency,
                "tokens": tokens,
                "success": success,
                "avg_latency": self.metrics["total_latency"] / self.metrics["request_count"]
            }
        })
        logger.info(f"MetricsService: Recorded request. Latency: {latency:.2f}s, Tokens: {tokens}")

    def get_summary(self) -> Dict[str, Any]:
        return {
            **self.metrics,
            "avg_latency": self.metrics["total_latency"] / max(1, self.metrics["request_count"])
        }

metrics_service = MetricsService()
