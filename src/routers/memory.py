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

@router.get("/{agent_id}/resume")
async def get_resume(agent_id: str):
    """Checks if there is a pending resume memory for the agent."""
    mgr = MemoryManager(agent_id=agent_id, system_prompt="")
    resume = mgr.memory.resume
    if resume:
        return {"has_resume": True, "resume_data": resume.model_dump(mode="json")}
    return {"has_resume": False}

@router.get("/{agent_id}/inspect")
async def inspect_memory(agent_id: str):
    """Returns a full inspection of all 5 memory lanes."""
    mgr = MemoryManager(agent_id=agent_id, system_prompt="")
    return {
        "agent_id": agent_id,
        "lanes": {
            "session": mgr.memory.session,
            "working": mgr.memory.working,
            "resume": mgr.memory.resume,
            "semantic": mgr.memory.semantic,
            "episodic": mgr.memory.episodic
        },
        "schema_version": mgr.memory.schema_version
    }

@router.post("/{agent_id}/learn")
async def add_learning(agent_id: str, req: LearnRequest):
# ... existing code ...
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
