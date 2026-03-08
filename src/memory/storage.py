import json
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.config import MEMORY_DIR

class MemoryEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class AgentMemory(BaseModel):
    agent_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    system_prompt: str
    entries: List[MemoryEntry] = []

class MemoryStorage:
    """Handles the persistent reading/writing of memory to the local file system."""
    
    def __init__(self, base_dir: Path = MEMORY_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_agent_path(self, agent_id: str, format: str = "json") -> Path:
        return self.base_dir / f"{agent_id}_memory.{format}"

    def save_memory(self, memory: AgentMemory, format: str = "json"):
        """Saves the AgentMemory object to disk in JSON or YAML format."""
        path = self._get_agent_path(memory.agent_id, format)
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
            
        return AgentMemory(**data)

    def delete_memory(self, agent_id: str, format: str = "json") -> bool:
        """Deletes the memory file for an agent."""
        path = self._get_agent_path(agent_id, format)
        if path.exists():
            path.unlink()
            return True
        return False
