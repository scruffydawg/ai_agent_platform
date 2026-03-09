from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any
from pydantic import BaseModel
from packages.services.browser_service import browser_service

from apps.api.response_models import SuccessResponse

router = APIRouter()

class SummarizeRequest(BaseModel):
    content: str
    query: str

@router.get("/scrape", response_model=SuccessResponse)
async def scrape_web_page(url: str):
    data = await browser_service.scrape_page(url)
    return SuccessResponse(data=data)

@router.post("/summarize", response_model=SuccessResponse)
async def summarize_research(request: SummarizeRequest):
    data = await browser_service.summarize_research(request.content, request.query)
    return SuccessResponse(data=data)
