from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from src.core.state import state_manager
from src.utils.storage_mapper import storage_mapper
import httpx
import os

from apps.api.response_models import SuccessResponse

router = APIRouter()

@router.post("/kill", response_model=SuccessResponse)
async def kill_all():
    """Emergency halt for all active agent processes."""
    state_manager.trigger_halt("API Request")
    return SuccessResponse(message="Halt signal broadcasted")

@router.post("/storage/init", response_model=SuccessResponse)
async def init_storage(path: str):
    """Initializes the standard AI directory structure at the given path."""
    if storage_mapper.set_root(path):
        success = storage_mapper.initialize_schema()
        if success:
            return SuccessResponse(message=f"Storage initialized at {path}")
        raise HTTPException(status_code=500, detail="Failed to create directory structure")
    raise HTTPException(status_code=400, detail="Invalid or inaccessible path")

@router.get("/ollama/models", response_model=SuccessResponse)
async def get_ollama_models():
    """Fetches the list of locally downloaded models from Ollama."""
    try:
        ollama_base = os.environ.get("LLM_BASE_URL", "http://localhost:11434").replace("/v1", "")
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{ollama_base}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [model.get("name") for model in data.get("models", [])]
                return SuccessResponse(data={"models": models})
            raise HTTPException(status_code=resp.status_code, detail="Ollama service error")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not connect to Ollama: {str(e)}")

@router.get("/help/snippets", response_model=SuccessResponse)
async def get_help_snippet(topic: str):
    """Contextual help lookup."""
    help_data = {
        "graph": "The Graph View shows your agent's thinking logic in real-time.",
        "canvas": "The Infinite Canvas is for visual brainstorming.",
        "settings": "Configure your AI Storage and connection strings here."
    }
    return SuccessResponse(data={"text": help_data.get(topic, "Help snippet not found.")})

@router.post("/canvas/event", response_model=SuccessResponse)
async def push_canvas_event(request: Request):
    """Broadcasts a manual event to the frontend canvas via EventBus."""
    from packages.services.event_service import event_service
    data = await request.json()
    event_service.publish(data)
    return SuccessResponse(message="Event broadcasted to observers")
