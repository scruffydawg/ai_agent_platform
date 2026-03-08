from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from src.memory.manager import MemoryManager
from src.core.state import state_manager

router = APIRouter(prefix="/memory", tags=["memory"])

class LearnRequest(BaseModel):
    agent_id: str
    fact: str
    context: Optional[str] = None
    is_user_pattern: bool = True

@router.get("/{agent_id}/learnings")
async def get_learnings(agent_id: str):
    """Returns all stored learnings for an agent."""
    # We initialize a temporary manager just to load the learning file
    mgr = MemoryManager(agent_id=agent_id, system_prompt="")
    return {
        "agent_id": agent_id,
        "user_patterns": mgr.learning.user_patterns,
        "self_patterns": mgr.learning.self_patterns,
        "summary": mgr.get_learning_summary()
    }

@router.post("/{agent_id}/learn")
async def add_learning(agent_id: str, req: LearnRequest):
    """Manually records a learning fact."""
    mgr = MemoryManager(agent_id=agent_id, system_prompt="")
    if req.is_user_pattern:
        mgr.record_user_learn(req.fact, req.context)
    else:
        mgr.record_self_learn(req.fact, req.context)
    return {"status": "success", "message": "Learning recorded."}

@router.delete("/{agent_id}/learnings")
async def clear_learnings(agent_id: str):
    """Resets all stored learnings for an agent."""
    from src.memory.storage import MemoryStorage, LearningMemory
    storage = MemoryStorage()
    empty_learning = LearningMemory(agent_id=agent_id)
    storage.save_learning(empty_learning)
    return {"status": "success", "message": "Learnings reset."}
