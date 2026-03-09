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

# ... other swarm routes can be migrated similarly
