import logging
from typing import Optional
from src.config import ALLOWED_SENDERS

logger = logging.getLogger(__name__)

class SenderWhitelist:
    """
    Gate 1: Deterministically reject unknown senders before processing any LLM logic.
    """
    def __init__(self, allowed_ids: list = None):
        self.allowed_ids = allowed_ids or ALLOWED_SENDERS

    def is_authorized(self, sender_id: str) -> bool:
        """
        Checks if the sender_id (phone number, telegram ID, username) is whitelisted.
        """
        if not sender_id:
            logger.warning("Security: Attempted access with null sender_id")
            return False
            
        is_val = sender_id.lower() in [s.lower() for s in self.allowed_ids]
        
        if not is_val:
            logger.error(f"Security Alert: Unauthorized sender '{sender_id}' blocked.")
            
        return is_val

# Global singleton for quick gate checks
whitelist = SenderWhitelist()
