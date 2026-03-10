from fastapi import APIRouter, Depends
from typing import Optional, List
from pydantic import BaseModel
from apps.api.response_models import SuccessResponse
from apps.api.settings import AppSettings, get_settings

from packages.services.config_service import config_service

router = APIRouter()

class ConfigUpdate(BaseModel):
    llm_url: Optional[str] = None
    default_model: Optional[str] = None
    searxng_url: Optional[str] = None
    qdrant_url: Optional[str] = None
    postgres_url: Optional[str] = None
    storagePath: Optional[str] = None

@router.get("/", response_model=SuccessResponse)
async def get_config():
    config_dict = config_service.dict()
    # Map backend keys to frontend expectations
    config_dict['llm_url'] = config_dict.get('llm_base_url', '')
    config_dict['storagePath'] = config_dict.get('storage_root', '')
    return SuccessResponse(data=config_dict)

@router.post("/", response_model=SuccessResponse)
async def update_config(config: ConfigUpdate):
    update_data = config.dict(exclude_unset=True)
    if 'llm_url' in update_data:
        update_data['llm_base_url'] = update_data.pop('llm_url')
    if 'storagePath' in update_data:
        update_data['storage_root'] = update_data.pop('storagePath')
    
    # Filter out empty strings so we don't nuke .env defaults
    clean_update = {k: v for k, v in update_data.items() if v != ""}
    config_service.update(clean_update)
    return SuccessResponse(message="Configuration updated successfully")
