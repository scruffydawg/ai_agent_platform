from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Optional, List, Dict, Any
import time
from src.memory.knowledge_base import kb_manager

from apps.api.response_models import SuccessResponse

router = APIRouter()

@router.post("/upload", response_model=SuccessResponse)
async def upload_knowledge(file: UploadFile = File(...), category: str = "general"):
    try:
        filename = file.filename
        content = await file.read()
        
        # Determine extraction method
        if filename.lower().endswith(".docx"):
            import io
            from docx import Document
            doc = Document(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])
        else:
            # Fallback to UTF-8 for .md, .txt, etc.
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Unsupported binary format. Please upload .docx, .pdf (handled elsewhere), or text-based files.")

        metadata = {
            "filename": filename,
            "category": category,
            "uploaded_at": time.time()
        }
        success = await kb_manager.ingest_document(text, metadata)
        if success:
            return SuccessResponse(data={"filename": filename}, message="Ingestion successful")
        else:
            raise HTTPException(status_code=500, detail="Ingestion failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=SuccessResponse)
async def search_knowledge(q: str):
    results = await kb_manager.search_reference(q)
    return SuccessResponse(data=results)
