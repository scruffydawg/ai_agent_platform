import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from apps.api.settings import get_settings

logger = logging.getLogger(__name__)

class EventService:
    """
    Centralized Event Service with Redis support and in-memory fallback.
    """
    def __init__(self):
        self._subscribers: List[Callable[[Dict[str, Any]], Awaitable[None]]] = []
        self._redis_client = None
        self._use_redis = False
        self._loop = asyncio.get_event_loop()

    async def initialize(self):
        settings = get_settings()
        # In a real setup we'd check settings.REDIS_URL
        # For now, we'll stick to in-memory but structured for Redis
        logger.info("EventService initialized in MEMORY mode.")

    async def publish(self, event: Dict[str, Any]):
        """
        Publishes an event to all subscribers.
        """
        if "timestamp" not in event:
            event["timestamp"] = asyncio.get_event_loop().time()
            
        logger.debug(f"Publishing event: {event.get('type')}")
        
        # In-memory broadcast
        for sub in self._subscribers[:]: # Use slice to avoid issues if sub list changes
            try:
                await sub(event)
            except Exception as e:
                logger.error(f"Error in event subscriber: {e}")

    def subscribe(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """
        Subscribes a callback to all events.
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

# Singleton
event_service = EventService()
