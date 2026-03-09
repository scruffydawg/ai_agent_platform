from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from pydantic import BaseModel
from packages.services.session_service import session_service

from apps.api.response_models import SuccessResponse

router = APIRouter()

class MessageRequest(BaseModel):
    role: str
    content: str

@router.get("/", response_model=SuccessResponse)
async def list_sessions():
    return SuccessResponse(data=session_service.list_sessions())

@router.post("/new", response_model=SuccessResponse)
async def start_new_session(name: Optional[str] = None):
    session_id = session_service.create_session(name)
    return SuccessResponse(data={"session_id": session_id}, message="Session created")

@router.get("/{session_id}", response_model=SuccessResponse)
async def load_session(session_id: str):
    data = session_service.load_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return SuccessResponse(data=data)

@router.post("/{session_id}/message", response_model=SuccessResponse)
async def add_message(session_id: str, request: MessageRequest):
    new_id = session_service.add_message(session_id, request.role, request.content)
    if not new_id:
        raise HTTPException(status_code=404, detail="Session not found")
    return SuccessResponse(data={"session_id": new_id}, message="Message added")
