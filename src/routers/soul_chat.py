from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from src.llm.client import LLMClient

router = APIRouter(prefix="/swarm", tags=["swarm"])

class SoulConsultRequest(BaseModel):
    agent_name: str
    current_soul: str
    messages: List[Dict[str, str]]

@router.post("/consult")
async def consult_soul(req: SoulConsultRequest):
    """
    Contextual AI assistant for refining agent souls and identities.
    """
    from src.config import DEFAULT_MODEL
    llm = LLMClient(model=DEFAULT_MODEL)
    
    system_prompt = f"""You are the 'Identity Architect', a specialist in engineering AI agent personas (Souls).
Your goal is to help the user refine, align, and evolve the "Soul" of an agent named '{req.agent_name}'.

The CURRENT SOUL script for {req.agent_name} is:
```markdown
{req.current_soul}
```

MISSION:
1. Help the user clarify the agent's core values, capabilities, and constraints.
2. Ensure {req.agent_name} stays aligned with the "Flute Path" (concise, efficient, harmonious).
3. Provide specific Markdown snippets if requested to update the soul.

Answer as a high-level architect. Be insightful, technical, and focused on persona stability."""

    # Build message chain
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    for msg in req.messages[-10:]:
        messages.append(msg)

    response = llm.generate(messages)
    
    if not response:
        raise HTTPException(status_code=500, detail="Identity consultation failed.")
        
    return {"status": "success", "response": response}
