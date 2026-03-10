from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from src.memory.manager import MemoryManager
from packages.services.memory_service import memory_service
from apps.api.response_models import SuccessResponse

router = APIRouter()

class LearnRequest(BaseModel):
    agent_id: str
    fact: str
    context: Optional[str] = None
    is_user_pattern: bool = True

@router.get("/{agent_id}/learnings", response_model=SuccessResponse)
async def get_learnings(agent_id: str):
    data = await memory_service.get_learnings(agent_id)
    return SuccessResponse(data=data)

@router.post("/{agent_id}/learn", response_model=SuccessResponse)
async def add_learning(agent_id: str, req: LearnRequest):
    await memory_service.record_learning(
        agent_id=agent_id,
        fact=req.fact,
        context=req.context,
        is_user=req.is_user_pattern
    )
    return SuccessResponse(message="Learning recorded")

@router.delete("/{agent_id}/learnings", response_model=SuccessResponse)
async def clear_learnings(agent_id: str):
    await memory_service.reset_learnings(agent_id)
    return SuccessResponse(message="Learnings reset")

@router.get("/{agent_id}/resume", response_model=Dict[str, Any])
async def get_resume(agent_id: str):
    """Checks if there is a pending resume memory for the agent."""
    mgr = MemoryManager(agent_id=agent_id, system_prompt="")
    await mgr.initialize()
    resume = mgr.memory.resume
    if resume:
        return {"has_resume": True, "resume_data": resume.model_dump(mode="json")}
    return {"has_resume": False}

@router.get("/{agent_id}/inspect", response_model=Dict[str, Any])
async def inspect_memory(agent_id: str):
    """Returns a full inspection of all 5 memory lanes."""
    mgr = MemoryManager(agent_id=agent_id, system_prompt="")
    await mgr.initialize()
    from packages.services.session_service import session_service
    
    # Merge active session messages into session lane for UI display
    session_data = session_service.load_session(agent_id)
    session_lane = [m.model_dump(mode="json") for m in mgr.memory.session]
    
    if session_data and "messages" in session_data:
        # Append recent session log entries to the lane
        for msg in session_data["messages"][-10:]:
            session_lane.append({
                "role": msg.get("role", "system"),
                "content": f"[SESSION]: {msg.get('content')}",
                "timestamp": session_data.get("last_updated", 0)
            })

    return {
        "status": "success",
        "agent_id": agent_id,
        "lanes": {
            "session": session_lane,
            "working": [m.model_dump(mode="json") for m in mgr.memory.working],
            "resume": mgr.memory.resume.model_dump(mode="json") if mgr.memory.resume else None,
            "semantic": [m.model_dump(mode="json") for m in mgr.memory.semantic],
            "episodic": [m.model_dump(mode="json") for m in mgr.memory.episodic]
        },
        "schema_version": mgr.memory.schema_version
    }
