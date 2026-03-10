import redis.asyncio as redis
from apps.api.settings import get_settings
import json
from typing import Optional, Any, List, Tuple
from src.utils.logger import logger

class QueueService:
    def __init__(self, queue_name: str = "orchestrator_requests"):
        self.settings = get_settings()
        self.client = redis.from_url(self.settings.redis_url, decode_responses=True)
        self.queue_name = queue_name

    async def enqueue(self, payload: Any, priority: int = 0):
        """
        Enqueues a payload with a given priority (lower is higher priority).
        """
        try:
            if isinstance(payload, (dict, list)):
                payload = json.dumps(payload)
            await self.client.zadd(self.queue_name, {payload: priority})
            logger.info(f"QueueService: Enqueued request with priority {priority}")
        except Exception as e:
            logger.error(f"QueueService: Enqueue failed: {e}")

    async def dequeue(self) -> Optional[Any]:
        """
        Dequeues the highest priority item.
        """
        try:
            # zpopmin returns a list of tuples (member, score)
            items = await self.client.zpopmin(self.queue_name, count=1)
            if items:
                content, score = items[0]
                try:
                    return json.loads(content)
                except:
                    return content
        except Exception as e:
            logger.error(f"QueueService: Dequeue failed: {e}")
        return None

    async def get_queue_size(self) -> int:
        try:
            return await self.client.zcard(self.queue_name)
        except Exception as e:
            logger.error(f"QueueService: Size check failed: {e}")
            return 0

queue_service = QueueService()
