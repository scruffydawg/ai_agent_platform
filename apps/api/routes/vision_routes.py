from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel
from packages.services.vision_service import vision_service

from apps.api.response_models import SuccessResponse

router = APIRouter()

@router.post("/screenshot", response_model=SuccessResponse)
async def capture_screen(confirm: bool = False, filename: Optional[str] = None):
    result = vision_service.take_screenshot(filename=filename)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return SuccessResponse(data=result)

@router.post("/webcam", response_model=SuccessResponse)
async def capture_camera(confirm: bool = False):
    result = vision_service.capture_webcam(confirm=confirm)
    return SuccessResponse(data=result)
