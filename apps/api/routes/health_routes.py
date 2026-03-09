import time
from fastapi import APIRouter, Depends
from apps.api.settings import AppSettings, get_settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0-alpha"
    }
