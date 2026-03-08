import threading
from typing import Dict, Optional, TypedDict

class SessionErrorState(TypedDict):
    error_hash: Optional[int]
    count: int
    is_blocked: bool

class StateManager:
    """
    Global state manager for the AI Agent Platform.
    Holds the strict Kill Switch to immediately halt all agent processes.
    """
    def __init__(self):
        self._halt_event = threading.Event()
        self._halt_reason = ""

    def trigger_halt(self, reason: str = "Manual User Override"):
        """Activates the global kill switch."""
        self._halt_reason = reason
        self._halt_event.set()
        print(f"\n[CRITICAL] SYSTEM HALTED: {reason}")

    def is_halted(self) -> bool:
        """Returns True if the system is halted."""
        return self._halt_event.is_set()

    def reset_halt(self):
        """Resets the global kill switch (use with extreme caution)."""
        self._halt_event.clear()
        self._halt_reason = ""
        print("\n[INFO] SYSTEM HALT RESET.")

        self._halt_reason = ""
        print("\n[INFO] SYSTEM HALT RESET.")

class RecoveryManager:
    """
    Tracks sequential failure loops for agents to prevent infinite hallucination loops.
    """
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._session_errors: Dict[str, SessionErrorState] = {} # session_id -> { "error_hash": count, "is_blocked": bool }

    def register_error(self, session_id: str, error_msg: str) -> bool:
        """
        Registers an error for a session. 
        Returns True if the circuit should BREAK (max retries reached).
        """
        if session_id not in self._session_errors:
            self._session_errors[session_id] = SessionErrorState(error_hash=None, count=0, is_blocked=False)
        
        state = self._session_errors[session_id]
        if state["is_blocked"]:
            return True # Already breached
            
        current_hash = hash(error_msg)
        
        if state["error_hash"] == current_hash:
            state["count"] += 1
        else:
            state["error_hash"] = current_hash
            state["count"] = 1 # Reset count for a NEW type of error
            
        if state["count"] >= self.max_retries:
            state["is_blocked"] = True
            return True
        return False
        
    def clear_errors(self, session_id: str):
        """Clears the error state for a session upon a successful turn."""
        if session_id in self._session_errors:
            self._session_errors[session_id] = SessionErrorState(error_hash=None, count=0, is_blocked=False)

    def is_blocked(self, session_id: str) -> bool:
        if session_id in self._session_errors:
            return self._session_errors[session_id]["is_blocked"]
        return False

# Singletons for application-wide access
state_manager = StateManager()
recovery_manager = RecoveryManager()
