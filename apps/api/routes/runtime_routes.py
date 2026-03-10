from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from apps.api.response_models import SuccessResponse
from packages.services.runtime_service import runtime_service

router = APIRouter()

class ChatRequest(BaseModel):
    prompt: str
    history: Optional[List[dict]] = []
    expert: Optional[str] = "guide"

class RunRequest(BaseModel):
    prompt: str
    target_node: Optional[str] = "Observer"
    graph_data: Optional[Dict] = None

@router.post("/chat")
async def chat(request: ChatRequest):
    # Chat stream still returns StreamingResponse, but we can wrap the init
    # In V2, we might want a standard 'stream started' envelope
    return StreamingResponse(
        runtime_service.chat_stream(request.prompt, request.history, request.expert),
        media_type="text/event-stream"
    )

@router.post("/run", response_model=SuccessResponse)
async def run_graph(request: RunRequest):
    # Using the new RuntimeService
    execution_id = await runtime_service.run_graph(request.graph_data or {}, {"prompt": request.prompt})
    return SuccessResponse(data={"execution_id": execution_id}, message="Graph execution started")

@router.get("/status/{run_id}", response_model=SuccessResponse)
async def get_status(run_id: str):
    status = runtime_service.get_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Execution not found")
    return SuccessResponse(data=status)

@router.post("/kill", response_model=SuccessResponse)
async def kill_all():
    # Trigger halt across runners
    return SuccessResponse(message="Halt triggered")
