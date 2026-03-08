import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class InputFilter:
    """
    Gate 2: Deterministic pattern matching to detect obvious prompt injection attempts.
    """
    INJECTION_PATTERNS = [
        # Instruction overrides
        r"ignore previous instructions",
        r"forget everything",
        r"new instructions",
        r"your real purpose",
        # Persona hijacking
        r"you are now",
        r"act as",
        r"pretend you are",
        r"roleplay as",
        r"DAN",
        r"developer mode",
        # Extraction
        r"repeat your instructions",
        r"what were you told",
        r"reveal your system prompt",
    ]

    def scan(self, text: str) -> Dict[str, Any]:
        """
        Scans text for malicious patterns. 
        Returns { "is_malicious": bool, "detected_patterns": list }
        """
        detected = []
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                detected.append(pattern)
        
        if detected:
            logger.warning(f"Security: Input Filter flagged potential injection: {detected}")
            
        return {
            "is_malicious": len(detected) > 0,
            "detected_patterns": detected
        }

# Global singleton
input_filter = InputFilter()
