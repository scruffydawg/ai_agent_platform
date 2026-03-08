# ============================================================
# SKILL: Web Search (SearXNG)
# ARCHETYPE: native
# ============================================================
# MCP_SERVERS:
#   - None (Direct HTTP to SearXNG)
# CODE_TOOLS:
#   - httpx (Async HTTP client)
# DOCS:
#   - https://docs.searxng.org/
# ============================================================
import httpx
from urllib.parse import urlparse
from src.config import SEARXNG_URL, SEARCH_DEFAULT_REGION, SEARCH_DEFAULT_LANGUAGE, SOURCE_TIERS
from src.utils.logger import logger

class WebSearch:
    def __init__(self):
        self.base_url = SEARXNG_URL

    def _rank_results(self, results):
        """Ranks results based on Multi-Tier Reputation logic."""
        ranked = []
        for res in results:
            url = res.get("url", "")
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            
            score = 0
            # Tier 1: Local Colorado Sources (highest priority)
            if any(local in domain for local in SOURCE_TIERS["tier_1_local"]):
                score += 100
            
            # Tier 3: Academic/Government (high reliability)
            elif any(domain.endswith(ext) for ext in SOURCE_TIERS["tier_3_academic"]):
                score += 80
                
            # Tier 2: Established National Sources
            elif any(national in domain for national in SOURCE_TIERS["tier_2_national"]):
                score += 60
            
            res["reputation_score"] = score
            ranked.append(res)
            
        # Sort by reputation score (desc) then by original search rank (implied by order)
        return sorted(ranked, key=lambda x: x["reputation_score"], reverse=True)

    async def search(self, query: str, limit: int = 5):
        """Perform a web search through the local SearXNG instance with geo-bias and reputation ranking."""
        refined_query = query
        if "colorado" not in query.lower() and "news" in query.lower():
            refined_query = f"{query} Colorado"

        # Search for a larger pool to allow for effective ranking
        params = {
            "q": refined_query,
            "format": "json",
            "engines": "google,bing,duckduckgo",
            "language": SEARCH_DEFAULT_LANGUAGE,
            "region": SEARCH_DEFAULT_REGION,
            "pageno": 1
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                raw_results = data.get("results", [])
                # Apply Reputation Ranking
                ranked_results = self._rank_results(raw_results)
                
                # Format the top results up to the limit
                final_results = []
                for res in ranked_results[:limit]:
                    final_results.append({
                        "title": res.get("title"),
                        "link": res.get("url"),
                        "snippet": res.get("content"),
                        "source_tier": "High" if res.get("reputation_score", 0) > 0 else "Neutral"
                    })
                return final_results
                
        except Exception as e:
            logger.error(f"SearXNG Search Error: {e}")
            return []

web_search = WebSearch()
