from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from src.memory.knowledge_base import kb_manager

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

class IngestRequest(BaseModel):
    content: str
    metadata: Dict[str, Any]

@router.post("/ingest")
async def ingest_to_kb(request: IngestRequest):
    """Ingests a document into the Knowledge Base."""
    success = await kb_manager.ingest_document(request.content, request.metadata)
    if success:
        return {"status": "success", "message": "Document ingested."}
    raise HTTPException(status_code=500, detail="Ingestion failed.")

@router.get("/search")
async def search_kb(q: str = Query(..., min_length=1), limit: int = 5):
    """Searches the Knowledge Base for reference materials."""
    results = await kb_manager.search_reference(q, limit)
    return {"results": results}
