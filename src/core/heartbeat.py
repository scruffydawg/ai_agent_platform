import threading
import time
from typing import Callable, Dict, Optional

from src.core.state import state_manager

class Heartbeat:
    """
    Central scheduler for triggered processes.
    Ensures no processes run unprompted. All background tasks must be registered here.
    """
    def __init__(self, interval_seconds: float = 1.0):
        self.interval = interval_seconds
        self._tasks: Dict[str, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def register_task(self, name: str, task_func: Callable):
        """Register a task to be executed on every heartbeat."""
        with self._lock:
            self._tasks[name] = task_func
            
    def unregister_task(self, name: str):
         with self._lock:
            if name in self._tasks:
                del self._tasks[name]

    def _loop(self):
        while self._running:
            # Check global kill switch
            if state_manager.is_halted():
                print("[Heartbeat] Global kill switch activated. Halting scheduler.")
                self.stop()
                break

            start_time = time.time()
            
            # Execute tasks
            with self._lock:
                for name, task in self._tasks.items():
                    try:
                        task()
                    except Exception as e:
                        print(f"[Heartbeat] Task '{name}' failed: {e}")

            # Sleep for remainder of interval
            elapsed = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed)
            time.sleep(sleep_time)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="HeartbeatThread")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

# Global singleton
heartbeat = Heartbeat()
