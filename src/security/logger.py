import asyncio
from src.utils.db import async_session
from src.security.models import SecurityEvent
from src.utils.logger import logger

class SecurityLogger:
    """
    Async logger for recording security events to Postgres.
    """
    async def log_event(self, event_type: str, severity: str, channel: str = "web", session_id: str = None, details: dict = None):
        try:
            async with async_session() as session:
                async with session.begin():
                    event = SecurityEvent(
                        event_type=event_type,
                        severity=severity,
                        channel=channel,
                        session_id=session_id,
                        details=details
                    )
                    session.add(event)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

# Global singleton
security_logger = SecurityLogger()
