from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any
from pydantic import BaseModel
from packages.services.browser_service import browser_service

router = APIRouter()

class SummarizeRequest(BaseModel):
    content: str
    query: str

@router.get("/scrape")
async def scrape_web_page(url: str):
    return await browser_service.scrape_page(url)

@router.post("/summarize")
async def summarize_research(request: SummarizeRequest):
    return await browser_service.summarize_research(request.content, request.query)
