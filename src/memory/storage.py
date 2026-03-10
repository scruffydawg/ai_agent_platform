import json
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.config import MEMORY_DIR

class MemoryLane(str):
    SESSION = "session"
    WORKING = "working"
    RESUME = "resume"
    SEMANTIC = "semantic"
    EPISODIC = "episodic"

class MemoryEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    role: str
    content: str
    lane: str = MemoryLane.SESSION
    source: str = "user"
    confidence: float = 1.0
    sensitivity: str = "internal" # internal, confidential, public
    schema_version: str = "3.0"
    metadata: Optional[Dict[str, Any]] = None

class LearningEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    fact: str
    context: Optional[str] = None
    relevance_score: float = 1.0
    confidence: float = 1.0
    source: str = "observation"

class LearningMemory(BaseModel):
    agent_id: str
    user_patterns: List[LearningEntry] = []
    self_patterns: List[LearningEntry] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = "3.0"

class AgentMemory(BaseModel):
    agent_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    system_prompt: str
    # 5-Lane Architecture
    session: List[MemoryEntry] = []
    working: List[MemoryEntry] = []
    resume: Optional[MemoryEntry] = None
    semantic: List[MemoryEntry] = []
    episodic: List[MemoryEntry] = []
    
    # Legacy support
    entries: List[MemoryEntry] = []
    schema_version: str = "3.0"

class MemoryStorage:
    """Handles the persistent reading/writing of memory to the local file system."""
    
    def __init__(self, base_dir: Path = MEMORY_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_agent_path(self, agent_id: str, format: str = "json") -> Path:
        return self.base_dir / f"{agent_id}_memory.{format}"

    def _get_learning_path(self, agent_id: str) -> Path:
        return self.base_dir / f"{agent_id}_learning.json"

    def save_memory(self, memory: AgentMemory, format: str = "json"):
        """Saves the AgentMemory object to disk in JSON or YAML format."""
        path = self._get_agent_path(memory.agent_id, format)
        memory.updated_at = datetime.utcnow()
        data = memory.model_dump(mode="json")
        
        if format == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        elif format == "yaml":
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported memory format: {format}")

    def load_memory(self, agent_id: str, format: str = "json") -> Optional[AgentMemory]:
        """Loads the AgentMemory object from disk."""
        path = self._get_agent_path(agent_id, format)
        
        if not path.exists():
            return None
            
        if format == "json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif format == "yaml":
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported memory format: {format}")
            
        # Migrate legacy data if needed
        if isinstance(data, dict) and "entries" in data and ("session" not in data or not data["session"]):
            # Simple migration: move all to session
            data["session"] = data.get("entries", [])
            
        return AgentMemory(**data)

    def delete_memory(self, agent_id: str, format: str = "json") -> bool:
        """Deletes the memory file for an agent."""
        path = self._get_agent_path(agent_id, format)
        if path.exists():
            path.unlink()
            return True
        return False

    def save_learning(self, learning: LearningMemory):
        """Saves agent learning patterns to disk."""
        path = self._get_learning_path(learning.agent_id)
        learning.updated_at = datetime.utcnow()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(learning.model_dump(mode="json"), f, indent=4)

    def load_learning(self, agent_id: str) -> LearningMemory:
        """Loads agent learning patterns from disk."""
        path = self._get_learning_path(agent_id)
        if not path.exists():
            return LearningMemory(agent_id=agent_id)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return LearningMemory(**data)
