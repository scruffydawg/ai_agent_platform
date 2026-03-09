from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Optional, List, Dict, Any
import time
from src.memory.knowledge_base import kb_manager

from apps.api.response_models import SuccessResponse

router = APIRouter()

@router.post("/upload", response_model=SuccessResponse)
async def upload_knowledge(file: UploadFile = File(...), category: str = "general"):
    try:
        content = await file.read()
        text = content.decode("utf-8")
        metadata = {
            "filename": file.filename,
            "category": category,
            "uploaded_at": time.time()
        }
        success = await kb_manager.ingest_document(text, metadata)
        if success:
            return SuccessResponse(data={"filename": file.filename}, message="Ingestion successful")
        else:
            raise HTTPException(status_code=500, detail="Ingestion failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=SuccessResponse)
async def search_knowledge(q: str):
    results = await kb_manager.search_reference(q)
    return SuccessResponse(data=results)
