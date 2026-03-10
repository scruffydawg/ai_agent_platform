import redis.asyncio as redis
from apps.api.settings import get_settings
import json
from typing import Optional, Any

class CacheEngine:
    def __init__(self):
        self.settings = get_settings()
        self.client = redis.from_url(self.settings.redis_url, decode_responses=True)

    async def set(self, key: str, value: Any, expire: int = 3600):
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.client.set(key, value, ex=expire)
        except Exception as e:
            from src.utils.logger import logger
            logger.warning(f"CacheEngine: SET failed for {key}: {e}")

    async def get(self, key: str) -> Optional[Any]:
        try:
            val = await self.client.get(key)
            if val:
                try:
                    return json.loads(val)
                except:
                    return val
        except Exception as e:
            from src.utils.logger import logger
            logger.warning(f"CacheEngine: GET failed for {key}: {e}")
        return None

    async def delete(self, key: str):
        try:
            await self.client.delete(key)
        except Exception as e:
            from src.utils.logger import logger
            logger.warning(f"CacheEngine: DELETE failed for {key}: {e}")
