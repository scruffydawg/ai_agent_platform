import re
import logging

logger = logging.getLogger(__name__)

class OutputFilter:
    """
    Gate 4: Redacts sensitive internal data before it leaves the system.
    """
    PATTERNS = {
        "IPs": r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b",
        "API_KEYS": r"(sk-[a-zA-Z0-9]{20,}|bearer\s+[a-zA-Z0-9]{20,})",
        "PATHS": r"(/home/[a-zA-Z0-9_-]+|/mnt/[a-zA-Z0-9_-]+|[A-Z]:\\[a-zA-Z0-9_-]+)",
        "SYSTEM_TAGS": r"\[(SYSTEM|RETRIEVED CONTEXT|USER MESSAGE|ADAPTIVE LEARNINGS)\]"
    }

    def redact(self, text: str) -> str:
        """
        Scans output and replaces sensitive patterns with redact markers.
        """
        redacted_text = text
        for label, pattern in self.PATTERNS.items():
            redacted_text = re.sub(pattern, f"[REDACTED {label}]", redacted_text, flags=re.IGNORECASE)
        
        if redacted_text != text:
            logger.info("Security: Output filter redacted sensitive content.")
            
        return redacted_text

# Global singleton
output_filter = OutputFilter()
