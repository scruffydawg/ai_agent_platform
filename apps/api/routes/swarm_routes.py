from fastapi import APIRouter, HTTPException, Request
from src.skills.swarm_telemetry import swarm_telemetry
import json

router = APIRouter()

@router.get("/local_status")
async def get_local_swarm_status():
    return await swarm_telemetry.get_local_stats()

@router.get("/status")
async def get_global_swarm_status():
    return await swarm_telemetry.get_swarm_status()

@router.get("/experts")
async def list_swarm_experts():
    from src.agents.persona_loader import persona_loader
    return {"experts": persona_loader.list_experts()}

@router.get("/expert/{name}")
async def get_expert_soul(name: str):
    from src.agents.persona_loader import persona_loader
    file_path = persona_loader.agents_dir / f"{name}.md"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Expert not found")
    with open(file_path, "r", encoding="utf-8") as f:
        return {"name": name, "soul": f.read()}

# ... other swarm routes can be migrated similarly
