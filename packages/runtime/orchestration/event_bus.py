import asyncio
from typing import Dict, Any, List, Optional, Callable

class EventBus:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.subscribers: List[Callable] = []

    async def publish(self, event: Dict[str, Any]):
        await self.queue.put(event)
        for sub in self.subscribers:
            try:
                await sub(event)
            except Exception:
                pass

    async def get_next(self):
        return await self.queue.get()

    def subscribe(self, callback: Callable):
        self.subscribers.append(callback)

event_bus = EventBus()
