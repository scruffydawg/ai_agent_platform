from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from packages.runtime.runtime_service import runtime_service
from src.core.state import state_manager

router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str
    history: Optional[List[dict]] = []
    expert: Optional[str] = "guide"

class RunRequest(BaseModel):
    prompt: str
    target_node: Optional[str] = "Observer"

@router.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        runtime_service.chat_stream(request.prompt, request.history, request.expert),
        media_type="text/event-stream"
    )

@router.post("/run")
async def run_graph(request: RunRequest):
    run_id = await runtime_service.start_run(session_id="default", prompt=request.prompt)
    return {"run_id": run_id, "status": "started"}

@router.get("/status/{run_id}")
async def get_status(run_id: str):
    # This should interact with a StateStore in Phase 10
    return {"status": "running", "run_id": run_id}

@router.post("/kill")
async def kill_all():
    state_manager.trigger_halt("Modular API Kill Request")
    return {"status": "halted"}
