from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Optional, List, Dict, Any
import time
from src.memory.knowledge_base import kb_manager

router = APIRouter()

@router.post("/upload")
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
            return {"status": "success", "filename": file.filename}
        else:
            raise HTTPException(status_code=500, detail="Ingestion failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_knowledge(q: str):
    results = await kb_manager.search_reference(q)
    return {"results": results}
