from typing import Dict, Any
import httpx
from src.skills.browser_proxy import browser_proxy
from apps.api.settings import get_settings

class BrowserService:
    def __init__(self):
        self.settings = get_settings()

    async def scrape_page(self, url: str) -> Dict[str, Any]:
        return await browser_proxy.scrape_page(url)

    async def summarize_research(self, content: str, query: str) -> Dict[str, Any]:
        prompt = f"Summarize the following research for the query: '{query}'\n\nContent: {content[:8000]}\n\nSummary:"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    self.settings.llm_base_url + "/completions",
                    json={
                        "model": self.settings.default_model,
                        "prompt": prompt,
                        "max_tokens": 500,
                        "temperature": 0.3
                    }
                )
                data = resp.json()
                return {"summary": data["choices"][0]["text"]}
        except Exception:
            return {"summary": "Failed to generate AI digest."}

browser_service = BrowserService()
