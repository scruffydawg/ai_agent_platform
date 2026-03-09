from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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
    data = memory_service.get_learnings(agent_id)
    return SuccessResponse(data=data)

@router.post("/{agent_id}/learn", response_model=SuccessResponse)
async def add_learning(agent_id: str, req: LearnRequest):
    memory_service.record_learning(
        agent_id=agent_id,
        fact=req.fact,
        context=req.context,
        is_user=req.is_user_pattern
    )
    return SuccessResponse(message="Learning recorded")

@router.delete("/{agent_id}/learnings", response_model=SuccessResponse)
async def clear_learnings(agent_id: str):
    memory_service.reset_learnings(agent_id)
    return SuccessResponse(message="Learnings reset")
