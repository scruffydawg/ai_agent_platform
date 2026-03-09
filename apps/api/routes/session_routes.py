from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from pydantic import BaseModel
from packages.services.session_service import session_service

router = APIRouter()

class MessageRequest(BaseModel):
    role: str
    content: str

@router.get("/")
async def list_sessions():
    return {"sessions": session_service.list_sessions()}

@router.post("/new")
async def start_new_session(name: Optional[str] = None):
    session_id = session_service.create_session(name)
    return {"session_id": session_id, "status": "created"}

@router.get("/{session_id}")
async def load_session(session_id: str):
    data = session_service.load_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data

@router.post("/{session_id}/message")
async def add_message(session_id: str, request: MessageRequest):
    new_id = session_service.add_message(session_id, request.role, request.content)
    if not new_id:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "session_id": new_id}
