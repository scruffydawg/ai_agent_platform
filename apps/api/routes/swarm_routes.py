from fastapi import APIRouter, HTTPException, Request
from src.skills.swarm_telemetry import swarm_telemetry
import json

from apps.api.response_models import SuccessResponse

router = APIRouter()

@router.get("/local_status", response_model=SuccessResponse)
async def get_local_swarm_status():
    data = await swarm_telemetry.get_local_stats()
    return SuccessResponse(data=data)

@router.get("/status", response_model=SuccessResponse)
async def get_global_swarm_status():
    data = await swarm_telemetry.get_swarm_status()
    return SuccessResponse(data=data)

@router.get("/experts", response_model=SuccessResponse)
async def list_swarm_experts():
    from src.agents.persona_loader import persona_loader
    data = persona_loader.list_experts()
    return SuccessResponse(data=data)

@router.get("/expert/{name}", response_model=SuccessResponse)
async def get_expert_soul(name: str):
    from src.agents.persona_loader import persona_loader
    file_path = persona_loader.agents_dir / f"{name}.md"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Expert not found")
    with open(file_path, "r", encoding="utf-8") as f:
        data = {"name": name, "soul": f.read()}
        return SuccessResponse(data=data)

@router.post("/expert/{name}", response_model=SuccessResponse)
async def update_expert_soul(name: str, request: Request):
    """Updates the Markdown soul of an agent."""
    body = await request.json()
    soul_content = body.get("soul")
    if not soul_content:
        raise HTTPException(status_code=400, detail="Missing soul content")
    
    from src.agents.persona_loader import persona_loader
    file_path = persona_loader.agents_dir / f"{name}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(soul_content)
    
    return SuccessResponse(data={"status": "success", "message": f"Soul for {name} updated."})

@router.post("/expert/spawn", response_model=SuccessResponse)
async def spawn_expert(request: Request):
    """Creates a new agent from a template."""
    body = await request.json()
    name = body.get("name", "NewAgent").capitalize()
    role = body.get("role", "Specialist")
    
    from src.agents.persona_loader import persona_loader
    file_path = persona_loader.agents_dir / f"{name}.md"
    if file_path.exists():
        raise HTTPException(status_code=400, detail="Agent already exists")
    
    template = f"""---
name: {name}
engine: qwen2.5-32b-instruct
---

# Role
{role}

# Guidelines
- Be concise.
- Follow the Flute Path logic.

# Skills
- None yet.

# Evolutionary Memory
- No entries.
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(template)
    
    return SuccessResponse(data={"status": "success", "name": name})

@router.delete("/expert/{name}", response_model=SuccessResponse)
async def delete_swarm_expert(name: str):
    """Removes an agent's Markdown soul file."""
    from src.agents.persona_loader import persona_loader
    file_path = persona_loader.agents_dir / f"{name}.md"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Expert not found")
    
    file_path.unlink()
    return SuccessResponse(data={"status": "success", "message": f"Expert {name} has been dissolved."})

@router.get("/flow", response_model=SuccessResponse)
async def get_swarm_flow():
    """Returns the persisted graph structure (nodes & edges)."""
    from src.server import SWARM_FLOW_FILE
    if not SWARM_FLOW_FILE.exists():
        return SuccessResponse(data={"nodes": [], "edges": []})
    with open(SWARM_FLOW_FILE, "r") as f:
        data = json.load(f)
        return SuccessResponse(data=data)

@router.post("/flow", response_model=SuccessResponse)
async def save_swarm_flow(request: Request):
    """Persists the graph structure from the ReactFlow UI."""
    from src.server import SWARM_FLOW_FILE
    data = await request.json()
    with open(SWARM_FLOW_FILE, "w") as f:
        json.dump(data, f, indent=4)
    return SuccessResponse(data={"status": "success"})

@router.post("/consult", response_model=SuccessResponse)
async def consult_soul(request: Request):
    """Contextual AI assistant for refining agent souls and identities."""
    from pydantic import BaseModel
    from src.llm.client import LLMClient
    from src.config import DEFAULT_MODEL
    
    body = await request.json()
    agent_name = body.get("agent_name")
    current_soul = body.get("current_soul")
    messages_history = body.get("messages", [])
    
    llm = LLMClient(model=DEFAULT_MODEL)
    
    system_prompt = f"""You are the 'Identity Architect', a specialist in engineering AI agent personas (Souls).
Your goal is to help the user refine, align, and evolve the "Soul" of an agent named '{agent_name}'.

The CURRENT SOUL script for {agent_name} is:
```markdown
{current_soul}
```

MISSION:
1. Help the user clarify the agent's core values, capabilities, and constraints.
2. Ensure {agent_name} stays aligned with the "Flute Path" (concise, efficient, harmonious).
3. Provide specific Markdown snippets if requested to update the soul.

Answer as a high-level architect. Be insightful, technical, and focused on persona stability."""

    # Build message chain
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    for msg in messages_history[-10:]:
        messages.append(msg)

    response = llm.generate(messages)
    
    if not response:
        raise HTTPException(status_code=500, detail="Identity consultation failed.")
        
    return SuccessResponse(data={"status": "success", "response": response})
