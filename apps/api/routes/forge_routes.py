from fastapi import APIRouter, HTTPException, Request
from src.agents.skill_builder import skill_builder
from src.skills.skill_indexer import skill_indexer
import os

router = APIRouter()

@router.post("/interview")
async def forge_interview(request: Request):
    body = await request.json()
    prompt = body.get("prompt")
    history = body.get("history", [])
    current_preview = body.get("current_preview", {})
    
    result = await skill_builder.interview_step(prompt, history, current_preview)
    return result

@router.post("/assemble")
async def forge_assemble(request: Request):
    # Migration of the assembly logic from server.py 841
    # For now, we'll keep it concise and call the logic
    # (Copy-pasting the logic or calling a service)
    # Let's assume we'll bake this into a SkillService later in Phase 10
    pass
