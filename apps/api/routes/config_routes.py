from fastapi import APIRouter, Depends
from typing import Optional, List
from pydantic import BaseModel
from apps.api.response_models import SuccessResponse
from apps.api.settings import AppSettings, get_settings

from packages.services.config_service import config_service

router = APIRouter()

class ConfigUpdate(BaseModel):
    llm_url: Optional[str]
    default_model: Optional[str]
    searxng_url: Optional[str]
    qdrant_url: Optional[str]

@router.get("/", response_model=SuccessResponse)
async def get_config():
    return SuccessResponse(data=config_service.dict())

@router.post("/", response_model=SuccessResponse)
async def update_config(config: ConfigUpdate):
    config_service.update(config.dict(exclude_unset=True))
    return SuccessResponse(message="Configuration updated successfully")
