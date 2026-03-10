import httpx
import asyncio
from fastapi import APIRouter, HTTPException
from apps.api.settings import get_settings
from apps.api.response_models import SuccessResponse
from src.utils.logger import logger

router = APIRouter()

@router.get("/models")
async def get_ollama_models():
    """Proxies Ollama models list to the frontend."""
    settings = get_settings()
    ollama_url = getattr(settings, "llm_base_url", "http://localhost:11434")
    
    # Strip /v1 if present for Ollama native API
    base_url = ollama_url.split('/v1')[0].rstrip('/')
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                return SuccessResponse(data={"models": models})
            else:
                return SuccessResponse(data={"models": ["gpt-3.5-turbo", "gpt-4"]})
    except Exception as e:
        logger.warning(f"Ollama not reachable at {base_url}: {e}")
        return SuccessResponse(data={"models": ["gpt-3.5-turbo", "gpt-4", "claude-3-opus"]})
