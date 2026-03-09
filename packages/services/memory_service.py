from pathlib import Path
from typing import List, Optional, Dict, Any
from src.memory.storage import MemoryStorage, LearningMemory, AgentMemory
from apps.api.settings import get_settings

class MemoryService:
    def __init__(self):
        settings = get_settings()
        self.base_dir = Path(settings.storage_root) / "memory"
        self.storage = MemoryStorage(base_dir=self.base_dir)

    def get_learnings(self, agent_id: str) -> Dict[str, Any]:
        from src.memory.manager import MemoryManager
        # Using MemoryManager for consistency with V1 logic
        mgr = MemoryManager(agent_id=agent_id, system_prompt="")
        return {
            "agent_id": agent_id,
            "user_patterns": mgr.learning.user_patterns,
            "self_patterns": mgr.learning.self_patterns,
            "summary": mgr.get_learning_summary()
        }

    def record_learning(self, agent_id: str, fact: str, context: Optional[str] = None, is_user: bool = True):
        from src.memory.manager import MemoryManager
        mgr = MemoryManager(agent_id=agent_id, system_prompt="")
        if is_user:
            mgr.record_user_learn(fact, context)
        else:
            mgr.record_self_learn(fact, context)

    def reset_learnings(self, agent_id: str):
        empty_learning = LearningMemory(agent_id=agent_id)
        self.storage.save_learning(empty_learning)

memory_service = MemoryService()
