import time
import asyncio
from typing import Dict, Any, Optional
import redis
from src.services.governance_service import governance_service
from src.utils.logger import logger

class SafetyGate:
    """
    Interceptor for Tool Execution.
    Coordinates governance checks and resource quota tracking.
    """
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            logger.info("SafetyGate: Connected to Redis for Quota Tracking.")
        except Exception as e:
            logger.error(f"SafetyGate: Redis connection failed: {e}. Rate limiting disabled.")
            self.redis = None

    async def validate_and_track(self, tool_name: str, arguments: Dict[str, Any], agent_id: str = "default") -> Dict[str, Any]:
        """
        Runs comprehensive safety checks and tracks resource usage.
        """
        # 1. Governance Policy Check
        gov_result = governance_service.validate_tool_call(tool_name, arguments)
        if not gov_result["allowed"]:
            return gov_result

        # 2. Resource Quota / Rate Limiting (Redis)
        if self.redis:
            try:
                quota_key = f"quota:{agent_id}:{tool_name}"
                count = self.redis.incr(quota_key)
                if count == 1:
                     self.redis.expire(quota_key, 60) # 1 minute window
                
                limit = 10 # Default: 10 calls per minute per tool
                if count > limit:
                    logger.warning(f"SafetyGate: Rate limit exceeded for {agent_id} on {tool_name}")
                    return {
                        "allowed": False,
                        "reason": f"Resource Quota Exceeded: Tool '{tool_name}' limited to {limit} calls/min.",
                        "requires_approval": False
                    }
            except Exception as e:
                logger.error(f"SafetyGate: Quota tracking error: {e}")

        return gov_result

# Global singleton
safety_gate = SafetyGate()
