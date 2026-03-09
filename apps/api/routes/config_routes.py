from fastapi import APIRouter, Depends
from apps.api.settings import AppSettings, get_settings
from pydantic import BaseModel

router = APIRouter()

class ConfigUpdate(BaseModel):
    llm_url: str
    default_model: str
    searxng_url: str
    qdrant_url: str

@router.get("/")
async def get_config(settings: AppSettings = Depends(get_settings)):
    return settings

@router.post("/")
async def update_config(config: ConfigUpdate, settings: AppSettings = Depends(get_settings)):
    # In V2, this will interact with a ConfigService
    return {"status": "success", "message": "Configuration updated (Service layer pending)"}
