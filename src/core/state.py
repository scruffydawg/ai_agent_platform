import threading

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

# Singleton for application-wide access
state_manager = StateManager()
