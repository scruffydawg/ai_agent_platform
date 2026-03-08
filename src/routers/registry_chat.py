from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from src.llm.client import LLMClient

router = APIRouter(prefix="/registry", tags=["registry"])

class ConsultRequest(BaseModel):
    tool_name: str
    tool_type: str  # "Skill" | "MCP Server" | "Code Tool"
    tool_description: str
    tool_source: Optional[str] = None
    tool_metadata: Optional[Dict[str, Any]] = None
    messages: List[Dict[str, str]]

@router.post("/consult")
async def consult_tool(req: ConsultRequest):
    """
    Simulates a contextual consultation chat with an expert on a specific tool.
    Returns a response from the LLM seeded with tool-specific context.
    """
    llm = LLMClient(model="gpt-3.5-turbo") # Or current default
    
    system_prompt = f"""You are the 'Guide Contextual Assistant', an expert on the following {req.tool_type}.
Your goal is to help the user understand, configure, or improve this tool.

TOOL NAME: {req.tool_name}
DESCRIPTION: {req.tool_description}
"""

    if req.tool_source:
        # Truncate source if it's too long for a single prompt, but usually skills are small enough
        system_prompt += f"\nSOURCE CODE / IMPLEMENTATION:\n```python\n{req.tool_source[:5000]}\n```\n"

    if req.tool_metadata:
        system_prompt += f"\nMETADATA / CONFIG:\n{req.tool_metadata}\n"

    system_prompt += "\nAnswer concisely and technically. If asked to 'update' or 'change' something, provide the code snippet but remind the user they must apply changes via the relevant editor."

    # Build message chain
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    for msg in req.messages[-10:]: # Recent 10 for context
        messages.append(msg)

    response = llm.generate(messages)
    
    if not response:
        raise HTTPException(status_code=500, detail="Failed to generate consultation response.")
        
    return {"status": "success", "response": response}
